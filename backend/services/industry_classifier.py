"""
Industry classifier service for classifying wallets by activity patterns
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


class IndustryClassifier:
    """Service for classifying wallets by activity patterns and calculating industry-specific scores"""
    
    # Industry categories
    INDUSTRIES = {
        'defi': {
            'keywords': ['swap', 'lend', 'borrow', 'stake', 'pool', 'vault', 'farm'],
            'contract_patterns': ['uniswap', 'aave', 'compound', 'maker'],
            'weight': 1.0,
        },
        'nft': {
            'keywords': ['mint', 'transfer', 'nft', 'erc721', 'erc1155'],
            'contract_patterns': ['opensea', 'rarible', 'nft'],
            'weight': 0.9,
        },
        'gaming': {
            'keywords': ['game', 'play', 'reward', 'quest'],
            'contract_patterns': ['game', 'gaming'],
            'weight': 0.85,
        },
        'dao': {
            'keywords': ['vote', 'proposal', 'governance', 'delegate'],
            'contract_patterns': ['governor', 'dao'],
            'weight': 1.1,
        },
        'bridge': {
            'keywords': ['bridge', 'deposit', 'withdraw', 'cross-chain'],
            'contract_patterns': ['bridge'],
            'weight': 0.95,
        },
        'dex': {
            'keywords': ['swap', 'trade', 'exchange', 'liquidity'],
            'contract_patterns': ['uniswap', 'sushiswap', 'dex'],
            'weight': 1.0,
        },
        'lending': {
            'keywords': ['lend', 'borrow', 'collateral', 'repay'],
            'contract_patterns': ['aave', 'compound', 'lending'],
            'weight': 1.05,
        },
    }
    
    # Minimum activity thresholds for classification
    MIN_TX_FOR_CLASSIFICATION = 5
    
    async def classify_wallet(
        self,
        address: str,
        session=None
    ) -> Dict[str, Any]:
        """
        Classify wallet by activity patterns
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Classification result with category and breakdown
        """
        try:
            from database.connection import get_session
            from database.models import Transaction, IndustryProfile
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            if session is None:
                async with get_session() as db_session:
                    return await self._classify_wallet(address, db_session)
            else:
                return await self._classify_wallet(address, session)
        except Exception as e:
            logger.error(f"Error classifying wallet: {e}", exc_info=True)
            return {
                "industry_category": "mixed",
                "activity_score": 0,
                "dominant_category": False,
                "category_breakdown": {},
            }
    
    async def _classify_wallet(self, address: str, session) -> Dict[str, Any]:
        """Classify wallet from database transactions"""
        from database.models import Transaction
        from sqlalchemy import select, func
        from datetime import datetime, timedelta
        
        try:
            # Get recent transactions (last 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await session.execute(
                select(Transaction)
                .where(
                    Transaction.wallet_address == address,
                    Transaction.block_timestamp >= cutoff_date
                )
            )
            transactions = result.scalars().all()
            
            if len(transactions) < self.MIN_TX_FOR_CLASSIFICATION:
                return {
                    "industry_category": "mixed",
                    "activity_score": 0,
                    "dominant_category": False,
                    "category_breakdown": {},
                }
            
            # Analyze transactions
            category_scores = defaultdict(float)
            
            for tx in transactions:
                tx_type_lower = (tx.tx_type or "").lower()
                contract_lower = (tx.contract_address or "").lower()
                
                # Score by transaction type
                for category, config in self.INDUSTRIES.items():
                    score = 0
                    
                    # Check keywords in tx_type
                    for keyword in config['keywords']:
                        if keyword in tx_type_lower:
                            score += 1.0
                    
                    # Check contract patterns
                    for pattern in config['contract_patterns']:
                        if pattern in contract_lower:
                            score += 2.0  # Contract matches are stronger signals
                    
                    if score > 0:
                        category_scores[category] += score * config['weight']
            
            # Calculate percentages
            total_score = sum(category_scores.values())
            if total_score == 0:
                return {
                    "industry_category": "mixed",
                    "activity_score": 0,
                    "dominant_category": False,
                    "category_breakdown": {},
                }
            
            category_breakdown = {
                cat: (score / total_score) * 100
                for cat, score in category_scores.items()
            }
            
            # Determine dominant category
            dominant_category = max(category_scores.items(), key=lambda x: x[1])[0]
            dominant_percentage = category_breakdown[dominant_category]
            
            # Calculate activity score (0-100)
            activity_score = min(100, int((len(transactions) / 100) * 100))
            
            # Determine if dominant (needs > 50% of activity)
            is_dominant = dominant_percentage > 50
            
            return {
                "industry_category": dominant_category if is_dominant else "mixed",
                "activity_score": activity_score,
                "dominant_category": is_dominant,
                "category_breakdown": category_breakdown,
            }
        except Exception as e:
            logger.error(f"Error in _classify_wallet: {e}", exc_info=True)
            return {
                "industry_category": "mixed",
                "activity_score": 0,
                "dominant_category": False,
                "category_breakdown": {},
            }
    
    async def get_industry_profile(
        self,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed industry profile for wallet
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Industry profile dict
        """
        try:
            from database.connection import get_session
            from database.models import IndustryProfile
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_industry_profile(address, db_session)
            else:
                return await self._get_industry_profile(address, session)
        except Exception as e:
            logger.error(f"Error getting industry profile: {e}", exc_info=True)
            return None
    
    async def _get_industry_profile(self, address: str, session) -> Optional[Dict[str, Any]]:
        """Get industry profile from database"""
        from database.models import IndustryProfile
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(IndustryProfile)
                .where(IndustryProfile.wallet_address == address)
            )
            profile = result.scalar_one_or_none()
            
            if profile:
                return {
                    "wallet_address": profile.wallet_address,
                    "industry_category": profile.industry_category,
                    "activity_score": profile.activity_score,
                    "dominant_category": profile.dominant_category,
                    "category_breakdown": profile.category_breakdown or {},
                    "last_analyzed_at": profile.last_analyzed_at.isoformat() if profile.last_analyzed_at else None,
                }
            
            return None
        except Exception as e:
            logger.error(f"Error in _get_industry_profile: {e}", exc_info=True)
            return None
    
    async def calculate_industry_score(
        self,
        address: str,
        category: str,
        base_score: int,
        session=None
    ) -> int:
        """
        Calculate industry-specific score
        
        Args:
            address: Wallet address
            category: Industry category
            base_score: Base credit score
            session: Database session (optional)
            
        Returns:
            Adjusted score based on industry
        """
        try:
            # Get industry weight
            industry_config = self.INDUSTRIES.get(category)
            if not industry_config:
                return base_score
            
            # Apply industry-specific adjustments
            # DeFi and Lending get slight boost (more established)
            # Gaming gets slight reduction (higher risk)
            adjustments = {
                'defi': 10,
                'lending': 15,
                'dao': 20,
                'dex': 10,
                'bridge': 5,
                'nft': 0,
                'gaming': -5,
                'mixed': 0,
            }
            
            adjustment = adjustments.get(category, 0)
            adjusted_score = base_score + adjustment
            
            # Cap at 0-1000
            return max(0, min(1000, adjusted_score))
        except Exception as e:
            logger.error(f"Error calculating industry score: {e}", exc_info=True)
            return base_score
    
    async def update_industry_profile(
        self,
        address: str,
        session=None
    ) -> bool:
        """
        Update industry profile for wallet
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            from database.connection import get_session
            from database.models import IndustryProfile
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._update_industry_profile(address, db_session)
            else:
                return await self._update_industry_profile(address, session)
        except Exception as e:
            logger.error(f"Error updating industry profile: {e}", exc_info=True)
            return False
    
    async def _update_industry_profile(self, address: str, session) -> bool:
        """Update industry profile in database"""
        from database.models import IndustryProfile
        from sqlalchemy import select
        
        try:
            # Classify wallet
            classification = await self._classify_wallet(address, session)
            
            # Get or create profile
            result = await session.execute(
                select(IndustryProfile)
                .where(IndustryProfile.wallet_address == address)
            )
            profile = result.scalar_one_or_none()
            
            if profile:
                # Update existing
                profile.industry_category = classification["industry_category"]
                profile.activity_score = classification["activity_score"]
                profile.dominant_category = classification["dominant_category"]
                profile.category_breakdown = classification["category_breakdown"]
                profile.last_analyzed_at = datetime.utcnow()
            else:
                # Create new
                profile = IndustryProfile(
                    wallet_address=address,
                    industry_category=classification["industry_category"],
                    activity_score=classification["activity_score"],
                    dominant_category=classification["dominant_category"],
                    category_breakdown=classification["category_breakdown"],
                    last_analyzed_at=datetime.utcnow()
                )
                session.add(profile)
            
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Error in _update_industry_profile: {e}", exc_info=True)
            await session.rollback()
            return False

