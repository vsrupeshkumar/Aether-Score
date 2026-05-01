import os
import time
from typing import Dict
from web3 import Web3
import requests
from models.score import WalletFeatures, ScoreResult
from services.oracle import QIEOracleService
from services.staking import StakingService
from utils.metrics import record_score_computation
from config.network import get_network_config, get_healthy_rpc_urls

class ScoringService:
    """AI-powered credit scoring service"""
    
    def __init__(self):
        # Use centralized network configuration
        self.network_config = get_network_config()
        healthy_rpcs = get_healthy_rpc_urls(self.network_config)
        self.rpc_url = healthy_rpcs[0] if healthy_rpcs else self.network_config.get_primary_rpc()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.explorer_url = self.network_config.explorer_url
        self.oracle_service = QIEOracleService()
        self.staking_service = StakingService()
    
    async def compute_score(self, address: str) -> Dict:
        """Compute credit score for a wallet address with oracle and staking integration"""
        start_time = time.time()
        try:
            # Fetch wallet data
            features = await self._extract_features(address)
            
            # Compute base score using rule-based algorithm
            base_score, base_risk_band, base_explanation = self._calculate_score(features)
            
            # Get oracle price and calculate penalty
            oracle_penalty = await self._calculate_oracle_penalty()
            
            # Get staking tier and boost
            staking_tier = self.staking_service.get_integration_tier(address)
            staking_boost = self.staking_service.calculate_staking_boost(staking_tier)
            staked_amount = self.staking_service.get_staked_amount(address)
            
            # Calculate final score
            final_score = max(0, min(1000, base_score - oracle_penalty + staking_boost))
            
            # Risk band can be improved by staking (if tier >= 2 and current band > 1)
            final_risk_band = base_risk_band
            if staking_tier >= 2 and base_risk_band > 1:
                final_risk_band = max(1, base_risk_band - 1)
            
            # Build explanation
            explanation_parts = [base_explanation]
            if oracle_penalty > 0:
                explanation_parts.append(f"Oracle volatility penalty: -{oracle_penalty} points")
            if staking_boost > 0:
                tier_names = {1: "Bronze", 2: "Silver", 3: "Gold"}
                explanation_parts.append(f"Staking boost ({tier_names.get(staking_tier, 'Unknown')} tier): +{staking_boost} points")
            if staking_tier >= 2 and final_risk_band < base_risk_band:
                explanation_parts.append(f"Risk band improved by staking tier")
            
            explanation = ". ".join(explanation_parts)
            
            # Log for debugging
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.debug(
                "Score calculation completed",
                extra={
                    "address": address,
                    "base_score": base_score,
                    "oracle_penalty": oracle_penalty,
                    "staking_boost": staking_boost,
                    "final_score": final_score,
                    "risk_band": f"{base_risk_band} -> {final_risk_band}",
                    "extra_data": {
                        "base_risk_band": base_risk_band,
                        "final_risk_band": final_risk_band,
                    }
                }
            )
            
            duration = time.time() - start_time
            
            # Record metrics
            record_score_computation(
                status="success",
                duration=duration,
                score=final_score
            )
            
            result = {
                "score": final_score,
                "baseScore": base_score,
                "riskBand": final_risk_band,
                "explanation": explanation,
                "stakingBoost": staking_boost,
                "oraclePenalty": oracle_penalty,
                "stakedAmount": staked_amount,
                "stakingTier": staking_tier,
                "features": features.__dict__ if features else None
            }
            
            # Track score history with explanation
            try:
                await self._save_score_history(
                    address,
                    final_score,
                    final_risk_band,
                    base_score,
                    staking_boost,
                    oracle_penalty,
                    explanation,
                    staking_tier
                )
            except Exception as e:
                logger.warning(f"Failed to save score history: {e}", exc_info=True)
            
            # Cache result
            from utils.cache import cache_score
            cache_score(address, result)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            record_score_computation(
                status="error",
                duration=duration
            )
            # Return default score on error
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(
                "Error computing score",
                exc_info=True,
                extra={
                    "address": address,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )
            return {
                "score": 500,
                "baseScore": 500,
                "riskBand": 2,
                "explanation": f"Error computing score: {str(e)}",
                "stakingBoost": 0,
                "oraclePenalty": 0,
                "stakedAmount": 0,
                "stakingTier": 0
            }
    
    async def _extract_features(self, address: str) -> WalletFeatures:
        """Extract features from wallet history"""
        try:
            # Get transaction count (simplified - in production, use proper indexer)
            tx_count = await self._get_tx_count(address)
            
            # Get balance
            balance = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_eth = self.w3.from_wei(balance, 'ether')
            
            # Feature extraction with QIE Oracle integration
            # Get price data from QIE Oracles
            eth_price = await self.oracle_service.get_price('ETH', 'crypto')
            usdt_price = await self.oracle_service.get_price('USDT', 'crypto')
            
            # Calculate volatility from QIE Oracle
            volatility = await self.oracle_service.get_volatility('ETH', days=30)
            
            # Estimate total volume (simplified - in production, analyze all transactions)
            total_volume = float(balance_eth) * (eth_price if eth_price else 2000)
            
            # Estimate stablecoin ratio (simplified - in production, analyze token holdings)
            # For demo, assume some stablecoin usage if balance is significant
            stablecoin_ratio = 0.3 if total_volume > 100 else 0.1
            
            # Calculate days active (simplified - in production, analyze first/last transaction)
            days_active = min(30, max(1, tx_count // 2))  # Estimate based on tx count
            
            features = WalletFeatures(
                tx_count=tx_count,
                total_volume=total_volume,
                stablecoin_ratio=stablecoin_ratio,
                avg_tx_value=float(balance_eth) / max(tx_count, 1),
                days_active=days_active,
                unique_contracts=min(10, tx_count // 5),  # Estimate
                max_drawdown=volatility * 0.5 if volatility else 0.1,  # Estimate from volatility
                volatility=volatility if volatility else 0.2
            )
            
            return features
        except Exception as e:
            # Return default features on error
            return WalletFeatures(
                tx_count=0,
                total_volume=0.0,
                stablecoin_ratio=0.0,
                avg_tx_value=0.0,
                days_active=0,
                unique_contracts=0,
                max_drawdown=0.0,
                volatility=0.0
            )
    
    async def _get_tx_count(self, address: str) -> int:
        """Get transaction count for address"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            count = self.w3.eth.get_transaction_count(checksum_address)
            return count
        except:
            return 0
    
    def _calculate_score(self, features: WalletFeatures) -> tuple[int, int, str]:
        """Calculate score and risk band from features"""
        score = 500  # Base score
        
        # Rule-based scoring (can be replaced with ML model)
        # Transaction activity (0-200 points)
        if features.tx_count > 100:
            score += 200
        elif features.tx_count > 50:
            score += 150
        elif features.tx_count > 20:
            score += 100
        elif features.tx_count > 10:
            score += 50
        
        # Volume (0-150 points)
        if features.total_volume > 1000:
            score += 150
        elif features.total_volume > 500:
            score += 100
        elif features.total_volume > 100:
            score += 50
        
        # Stablecoin ratio (0-100 points)
        if features.stablecoin_ratio > 0.7:
            score += 100
        elif features.stablecoin_ratio > 0.5:
            score += 50
        
        # Activity duration (0-100 points)
        if features.days_active > 90:
            score += 100
        elif features.days_active > 30:
            score += 50
        
        # Volatility penalty (0-150 points deduction)
        if features.volatility > 0.5:
            score -= 150
        elif features.volatility > 0.3:
            score -= 100
        elif features.volatility > 0.2:
            score -= 50
        
        # Clamp score to 0-1000
        score = max(0, min(1000, score))
        
        # Determine risk band
        if score >= 750:
            risk_band = 1  # Low risk
            explanation = "Low risk: High transaction activity, good volume, stable portfolio"
        elif score >= 500:
            risk_band = 2  # Medium risk
            explanation = "Medium risk: Moderate activity and volume"
        elif score >= 250:
            risk_band = 3  # High risk
            explanation = "High risk: Low activity or high volatility"
        else:
            risk_band = 3  # High risk
            explanation = "High risk: Very low score, limited history"
        
        return score, risk_band, explanation
    
    async def _calculate_oracle_penalty(self) -> int:
        """
        Calculate penalty based on oracle volatility
        For demo: simple rule based on price stability
        """
        try:
            oracle_address = os.getenv("QIE_ORACLE_USD_ADDR")
            if not oracle_address or oracle_address == "0x0000000000000000000000000000000000000000":
                return 0
            
            # Fetch current price
            current_price = await self.oracle_service.fetchOraclePrice(oracle_address)
            if not current_price:
                return 0
            
            # For demo: simple volatility check
            # In production, would compare against historical prices
            # For now, return small penalty if price seems volatile (placeholder logic)
            # This is a simplified demo - real implementation would track price history
            volatility = await self.oracle_service.get_volatility('ETH', days=30)
            
            if volatility and volatility > 0.3:
                return 50  # High volatility penalty
            elif volatility and volatility > 0.2:
                return 25  # Medium volatility penalty
            else:
                return 0   # Low volatility, no penalty
        except Exception as e:
            print(f"Error calculating oracle penalty: {e}")
            return 0
    
    async def _save_score_history(
        self,
        address: str,
        final_score: int,
        final_risk_band: int,
        base_score: int,
        staking_boost: int,
        oracle_penalty: int,
        explanation: str,
        staking_tier: int
    ):
        """Save score history with explanation"""
        try:
            from database.connection import get_session
            from database.repositories import ScoreHistoryRepository
            from services.score_explanation import ScoreExplanationService
            
            async with get_session() as session:
                # Get previous score
                previous_score_entry = await ScoreHistoryRepository.get_latest_score(session, address)
                previous_score = previous_score_entry.score if previous_score_entry else None
                
                # Determine change reason
                change_reason = ScoreExplanationService.determine_change_reason(
                    old_score=previous_score,
                    new_score=final_score,
                    base_score=base_score,
                    staking_boost=staking_boost,
                    oracle_penalty=oracle_penalty,
                    metadata={
                        "staking_tier": staking_tier,
                        "boost": staking_boost,
                        "penalty": oracle_penalty,
                    }
                )
                
                # Generate explanation if not already generated or if it's the first score
                if not explanation or previous_score is None:
                    explanation = ScoreExplanationService.generate_explanation(
                        old_score=previous_score,
                        new_score=final_score,
                        change_reason=change_reason,
                        metadata={
                            "boost": staking_boost,
                            "penalty": oracle_penalty,
                            "tier": staking_tier,
                        }
                    )
                
                # Save to history
                await ScoreHistoryRepository.add_history(
                    session=session,
                    wallet_address=address,
                    score=final_score,
                    risk_band=final_risk_band,
                    previous_score=previous_score,
                    explanation=explanation,
                    change_reason=change_reason
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to save score history: {e}", exc_info=True)
            # Don't raise - history tracking is non-critical

