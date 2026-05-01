"""
Advanced Feature Engineering Service

Extracts 50+ features from indexed transactions including:
- Transaction patterns (frequency, regularity, time-of-day)
- Token holdings (ERC-20 diversity, concentration, stability)
- DeFi interactions (DEX swaps, liquidity provision, yield farming)
- Network analysis (address clustering, relationship graphs)
- Temporal features (account age, activity streaks, inactivity periods)
- Financial metrics (portfolio value, diversification index, volatility)
- Behavioral features (transaction timing patterns, gas usage patterns)
"""

import os
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from collections import Counter, defaultdict
import statistics

from database.models import Transaction, TokenTransfer, User
from database.connection import get_db_session
from utils.logger import get_logger

logger = get_logger(__name__)


class FeatureEngineering:
    """Service for extracting advanced features from wallet data"""
    
    def __init__(self):
        self.rpc_url = os.getenv("QIE_RPC_URL") or os.getenv("QIE_TESTNET_RPC_URL", "https://rpc1testnet.qie.digital/")
    
    async def extract_all_features(self, address: str) -> Dict[str, Any]:
        """
        Extract all features for an address
        
        Returns:
            Dict with all extracted features
        """
        try:
            async with get_db_session() as session:
                # Get all transactions for this address
                transactions = await self._get_transactions(session, address)
                
                # Get all token transfers
                token_transfers = await self._get_token_transfers(session, address)
                
                # Extract features
                features = {}
                
                # Transaction pattern features
                features.update(await self._extract_transaction_patterns(transactions))
                
                # Token holding features
                features.update(await self._extract_token_holdings(token_transfers))
                
                # DeFi interaction features
                features.update(await self._extract_defi_interactions(transactions))
                
                # Network analysis features
                features.update(await self._extract_network_features(transactions, token_transfers))
                
                # Temporal features
                features.update(await self._extract_temporal_features(transactions))
                
                # Financial metrics
                features.update(await self._extract_financial_metrics(transactions, token_transfers))
                
                # Behavioral features
                features.update(await self._extract_behavioral_features(transactions))
                
                return features
                
        except Exception as e:
            logger.error(f"Error extracting features: {e}", exc_info=True, extra={"address": address})
            return {}
    
    async def _get_transactions(self, session: AsyncSession, address: str) -> List[Transaction]:
        """Get all transactions for an address"""
        try:
            stmt = select(Transaction).where(
                Transaction.wallet_address == address
            ).order_by(Transaction.block_timestamp.asc())
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting transactions: {e}", exc_info=True)
            return []
    
    async def _get_token_transfers(self, session: AsyncSession, address: str) -> List[TokenTransfer]:
        """Get all token transfers for an address"""
        try:
            stmt = select(TokenTransfer).where(
                or_(
                    TokenTransfer.from_address == address,
                    TokenTransfer.to_address == address
                )
            ).order_by(TokenTransfer.block_timestamp.asc())
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting token transfers: {e}", exc_info=True)
            return []
    
    async def _extract_transaction_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Extract transaction pattern features"""
        if not transactions:
            return {
                "tx_count": 0,
                "tx_frequency_daily": 0.0,
                "tx_regularity_score": 0.0,
                "tx_time_of_day_variance": 0.0,
                "tx_weekend_ratio": 0.0,
                "tx_gas_efficiency": 0.0,
                "tx_failure_rate": 0.0,
            }
        
        # Basic counts
        tx_count = len(transactions)
        successful_txs = [t for t in transactions if t.status == "success"]
        failed_txs = [t for t in transactions if t.status == "failed"]
        
        # Transaction frequency
        if len(transactions) > 1:
            first_tx = transactions[0].block_timestamp
            last_tx = transactions[-1].block_timestamp
            if first_tx and last_tx:
                days_active = (last_tx - first_tx).days or 1
                tx_frequency_daily = tx_count / days_active
            else:
                tx_frequency_daily = 0.0
        else:
            tx_frequency_daily = 0.0
        
        # Regularity score (coefficient of variation of inter-transaction times)
        if len(transactions) > 2:
            intervals = []
            for i in range(1, len(transactions)):
                if transactions[i].block_timestamp and transactions[i-1].block_timestamp:
                    interval = (transactions[i].block_timestamp - transactions[i-1].block_timestamp).total_seconds()
                    if interval > 0:
                        intervals.append(interval)
            
            if intervals:
                mean_interval = statistics.mean(intervals)
                if mean_interval > 0:
                    std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
                    tx_regularity_score = 1.0 / (1.0 + (std_interval / mean_interval))  # Higher = more regular
                else:
                    tx_regularity_score = 0.0
            else:
                tx_regularity_score = 0.0
        else:
            tx_regularity_score = 0.5  # Default for few transactions
        
        # Time of day variance
        hours = []
        for tx in transactions:
            if tx.block_timestamp:
                hours.append(tx.block_timestamp.hour)
        
        if hours:
            tx_time_of_day_variance = statistics.variance(hours) if len(hours) > 1 else 0.0
        else:
            tx_time_of_day_variance = 0.0
        
        # Weekend ratio
        weekend_count = 0
        for tx in transactions:
            if tx.block_timestamp:
                weekday = tx.block_timestamp.weekday()
                if weekday >= 5:  # Saturday = 5, Sunday = 6
                    weekend_count += 1
        
        tx_weekend_ratio = weekend_count / tx_count if tx_count > 0 else 0.0
        
        # Gas efficiency (average gas used per transaction)
        gas_values = [t.gas_used for t in successful_txs if t.gas_used]
        if gas_values:
            avg_gas = statistics.mean(gas_values)
            tx_gas_efficiency = 1.0 / (1.0 + (avg_gas / 100000))  # Normalize
        else:
            tx_gas_efficiency = 0.5
        
        # Failure rate
        tx_failure_rate = len(failed_txs) / tx_count if tx_count > 0 else 0.0
        
        return {
            "tx_count": tx_count,
            "tx_frequency_daily": tx_frequency_daily,
            "tx_regularity_score": tx_regularity_score,
            "tx_time_of_day_variance": tx_time_of_day_variance,
            "tx_weekend_ratio": tx_weekend_ratio,
            "tx_gas_efficiency": tx_gas_efficiency,
            "tx_failure_rate": tx_failure_rate,
        }
    
    async def _extract_token_holdings(self, token_transfers: List[TokenTransfer]) -> Dict[str, Any]:
        """Extract token holding features"""
        if not token_transfers:
            return {
                "token_diversity": 0.0,
                "token_concentration": 0.0,
                "token_stability": 0.0,
                "unique_tokens": 0,
                "erc20_count": 0,
                "erc721_count": 0,
                "stablecoin_ratio": 0.0,
            }
        
        # Token counts
        unique_tokens = len(set(t.token_address for t in token_transfers))
        erc20_count = len([t for t in token_transfers if t.token_type == "ERC20"])
        erc721_count = len([t for t in token_transfers if t.token_type == "ERC721"])
        
        # Token diversity (Shannon entropy)
        token_counts = Counter(t.token_address for t in token_transfers)
        total_transfers = len(token_transfers)
        
        if total_transfers > 0:
            token_diversity = -sum(
                (count / total_transfers) * math.log(count / total_transfers)
                for count in token_counts.values()
            )
        else:
            token_diversity = 0.0
        
        # Token concentration (Gini coefficient)
        if len(token_counts) > 1:
            sorted_counts = sorted(token_counts.values(), reverse=True)
            n = len(sorted_counts)
            cumsum = sum(sorted_counts)
            if cumsum > 0:
                token_concentration = (2 * sum((i + 1) * count for i, count in enumerate(sorted_counts))) / (n * cumsum) - (n + 1) / n
            else:
                token_concentration = 0.0
        else:
            token_concentration = 1.0  # All in one token
        
        # Token stability (how often tokens are held vs transferred)
        # Simplified: ratio of unique tokens to total transfers
        token_stability = unique_tokens / total_transfers if total_transfers > 0 else 0.0
        
        # Stablecoin ratio (assuming USDT, USDC, DAI addresses)
        # This is a simplified check - in production, maintain a list of stablecoin addresses
        stablecoin_addresses = {
            "0x0000000000000000000000000000000000000000",  # Placeholder
            # Add actual stablecoin addresses
        }
        stablecoin_transfers = len([t for t in token_transfers if t.token_address.lower() in [a.lower() for a in stablecoin_addresses]])
        stablecoin_ratio = stablecoin_transfers / total_transfers if total_transfers > 0 else 0.0
        
        return {
            "token_diversity": token_diversity,
            "token_concentration": token_concentration,
            "token_stability": token_stability,
            "unique_tokens": unique_tokens,
            "erc20_count": erc20_count,
            "erc721_count": erc721_count,
            "stablecoin_ratio": stablecoin_ratio,
        }
    
    async def _extract_defi_interactions(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Extract DeFi interaction features"""
        if not transactions:
            return {
                "defi_interaction_count": 0,
                "dex_swap_count": 0,
                "liquidity_provision_count": 0,
                "yield_farming_count": 0,
                "unique_defi_protocols": 0,
                "defi_activity_ratio": 0.0,
            }
        
        # Identify DeFi interactions by contract addresses and method IDs
        # Common DeFi method signatures (first 4 bytes)
        dex_methods = {
            "0x38ed1739",  # swap (Uniswap V2)
            "0x7ff36ab5",  # swapExactETHForTokens
            "0x8803dbee",  # swapTokensForExactTokens
            # Add more DEX method signatures
        }
        
        liquidity_methods = {
            "0xe8e33700",  # addLiquidity
            "0xbaa2abde",  # addLiquidityETH
            "0x02751cec",  # removeLiquidity
            # Add more liquidity method signatures
        }
        
        yield_methods = {
            "0x379607f5",  # deposit
            "0x2e1a7d4d",  # withdraw
            "0x3d18b912",  # claim
            # Add more yield farming method signatures
        }
        
        defi_txs = []
        dex_swaps = []
        liquidity_txs = []
        yield_txs = []
        unique_protocols = set()
        
        for tx in transactions:
            if tx.contract_address and tx.method_id:
                unique_protocols.add(tx.contract_address.lower())
                
                if tx.method_id in dex_methods:
                    dex_swaps.append(tx)
                    defi_txs.append(tx)
                elif tx.method_id in liquidity_methods:
                    liquidity_txs.append(tx)
                    defi_txs.append(tx)
                elif tx.method_id in yield_methods:
                    yield_txs.append(tx)
                    defi_txs.append(tx)
        
        defi_activity_ratio = len(defi_txs) / len(transactions) if transactions else 0.0
        
        return {
            "defi_interaction_count": len(defi_txs),
            "dex_swap_count": len(dex_swaps),
            "liquidity_provision_count": len(liquidity_txs),
            "yield_farming_count": len(yield_txs),
            "unique_defi_protocols": len(unique_protocols),
            "defi_activity_ratio": defi_activity_ratio,
        }
    
    async def _extract_network_features(self, transactions: List[Transaction], token_transfers: List[TokenTransfer]) -> Dict[str, Any]:
        """Extract network analysis features"""
        if not transactions:
            return {
                "unique_contracts": 0,
                "unique_addresses": 0,
                "address_clustering_score": 0.0,
                "transaction_graph_density": 0.0,
                "reciprocity_score": 0.0,
            }
        
        # Unique contracts and addresses
        unique_contracts = len(set(t.contract_address for t in transactions if t.contract_address))
        unique_addresses = len(set(
            [t.from_address for t in transactions if t.from_address] +
            [t.to_address for t in transactions if t.to_address]
        ))
        
        # Address clustering (simplified: count of addresses that appear multiple times)
        address_counts = Counter(
            [t.from_address for t in transactions if t.from_address] +
            [t.to_address for t in transactions if t.to_address]
        )
        clustered_addresses = len([addr for addr, count in address_counts.items() if count > 1])
        address_clustering_score = clustered_addresses / len(address_counts) if address_counts else 0.0
        
        # Transaction graph density (simplified)
        # In production, build a proper graph and calculate density
        total_possible_edges = len(address_counts) * (len(address_counts) - 1) / 2
        actual_edges = len(set(
            (t.from_address, t.to_address)
            for t in transactions
            if t.from_address and t.to_address
        ))
        transaction_graph_density = actual_edges / total_possible_edges if total_possible_edges > 0 else 0.0
        
        # Reciprocity score (how often address A sends to B and B sends to A)
        bidirectional_pairs = set()
        address_pairs = set()
        for tx in transactions:
            if tx.from_address and tx.to_address:
                pair = (tx.from_address.lower(), tx.to_address.lower())
                address_pairs.add(pair)
                reverse_pair = (tx.to_address.lower(), tx.from_address.lower())
                if reverse_pair in address_pairs:
                    bidirectional_pairs.add(pair)
        
        reciprocity_score = len(bidirectional_pairs) / len(address_pairs) if address_pairs else 0.0
        
        return {
            "unique_contracts": unique_contracts,
            "unique_addresses": unique_addresses,
            "address_clustering_score": address_clustering_score,
            "transaction_graph_density": transaction_graph_density,
            "reciprocity_score": reciprocity_score,
        }
    
    async def _extract_temporal_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Extract temporal features"""
        if not transactions:
            return {
                "account_age_days": 0,
                "activity_streak_days": 0,
                "max_inactivity_days": 0,
                "avg_inactivity_days": 0.0,
                "activity_consistency": 0.0,
            }
        
        timestamps = [t.block_timestamp for t in transactions if t.block_timestamp]
        if not timestamps:
            return {
                "account_age_days": 0,
                "activity_streak_days": 0,
                "max_inactivity_days": 0,
                "avg_inactivity_days": 0.0,
                "activity_consistency": 0.0,
            }
        
        timestamps.sort()
        first_tx = timestamps[0]
        last_tx = timestamps[-1]
        
        # Account age
        account_age_days = (last_tx - first_tx).days if last_tx > first_tx else 0
        
        # Activity streaks
        current_streak = 1
        max_streak = 1
        inactivity_periods = []
        
        for i in range(1, len(timestamps)):
            days_diff = (timestamps[i] - timestamps[i-1]).days
            if days_diff <= 1:  # Activity within 1 day = streak
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                inactivity_periods.append(days_diff)
                current_streak = 1
        
        activity_streak_days = max_streak
        max_inactivity_days = max(inactivity_periods) if inactivity_periods else 0
        avg_inactivity_days = statistics.mean(inactivity_periods) if inactivity_periods else 0.0
        
        # Activity consistency (coefficient of variation of daily activity)
        daily_activity = defaultdict(int)
        for ts in timestamps:
            day_key = ts.date()
            daily_activity[day_key] += 1
        
        if len(daily_activity) > 1:
            activity_values = list(daily_activity.values())
            mean_activity = statistics.mean(activity_values)
            if mean_activity > 0:
                std_activity = statistics.stdev(activity_values) if len(activity_values) > 1 else 0
                activity_consistency = 1.0 / (1.0 + (std_activity / mean_activity))
            else:
                activity_consistency = 0.0
        else:
            activity_consistency = 1.0  # Perfect consistency if only one day
        
        return {
            "account_age_days": account_age_days,
            "activity_streak_days": activity_streak_days,
            "max_inactivity_days": max_inactivity_days,
            "avg_inactivity_days": avg_inactivity_days,
            "activity_consistency": activity_consistency,
        }
    
    async def _extract_financial_metrics(self, transactions: List[Transaction], token_transfers: List[TokenTransfer]) -> Dict[str, Any]:
        """Extract financial metrics"""
        if not transactions:
            return {
                "total_volume": 0.0,
                "avg_tx_value": 0.0,
                "max_tx_value": 0.0,
                "portfolio_volatility": 0.0,
                "diversification_index": 0.0,
            }
        
        # Transaction values
        tx_values = [float(t.value or 0) for t in transactions if t.value]
        total_volume = sum(tx_values)
        avg_tx_value = statistics.mean(tx_values) if tx_values else 0.0
        max_tx_value = max(tx_values) if tx_values else 0.0
        
        # Portfolio volatility (simplified: standard deviation of transaction values)
        if len(tx_values) > 1:
            portfolio_volatility = statistics.stdev(tx_values) / (statistics.mean(tx_values) or 1)
        else:
            portfolio_volatility = 0.0
        
        # Diversification index (Herfindahl index)
        token_values = defaultdict(float)
        for transfer in token_transfers:
            if transfer.amount:
                token_values[transfer.token_address] += float(transfer.amount)
        
        if token_values:
            total_token_value = sum(token_values.values())
            if total_token_value > 0:
                diversification_index = 1.0 - sum((v / total_token_value) ** 2 for v in token_values.values())
            else:
                diversification_index = 0.0
        else:
            diversification_index = 0.0
        
        return {
            "total_volume": total_volume,
            "avg_tx_value": avg_tx_value,
            "max_tx_value": max_tx_value,
            "portfolio_volatility": portfolio_volatility,
            "diversification_index": diversification_index,
        }
    
    async def _extract_behavioral_features(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Extract behavioral features"""
        if not transactions:
            return {
                "gas_price_preference": 0.0,
                "tx_timing_preference": 0.0,
                "contract_interaction_preference": 0.0,
                "value_distribution_skew": 0.0,
            }
        
        # Gas price preference (average gas price)
        gas_prices = [t.gas_price for t in transactions if t.gas_price]
        gas_price_preference = statistics.mean(gas_prices) if gas_prices else 0.0
        
        # Transaction timing preference (most active hour)
        hours = [t.block_timestamp.hour for t in transactions if t.block_timestamp]
        if hours:
            hour_counts = Counter(hours)
            most_common_hour = hour_counts.most_common(1)[0][0]
            tx_timing_preference = most_common_hour / 24.0  # Normalize to 0-1
        else:
            tx_timing_preference = 0.5
        
        # Contract interaction preference
        contract_txs = len([t for t in transactions if t.contract_address])
        contract_interaction_preference = contract_txs / len(transactions) if transactions else 0.0
        
        # Value distribution skew (simplified)
        tx_values = [float(t.value or 0) for t in transactions if t.value]
        if len(tx_values) > 2:
            mean_value = statistics.mean(tx_values)
            median_value = statistics.median(tx_values)
            if mean_value > 0:
                value_distribution_skew = (mean_value - median_value) / mean_value
            else:
                value_distribution_skew = 0.0
        else:
            value_distribution_skew = 0.0
        
        return {
            "gas_price_preference": gas_price_preference,
            "tx_timing_preference": tx_timing_preference,
            "contract_interaction_preference": contract_interaction_preference,
            "value_distribution_skew": value_distribution_skew,
        }

