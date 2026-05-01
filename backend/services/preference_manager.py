"""
Preference manager service for managing user loan preferences
"""
from typing import Dict, Optional, Any, List
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class PreferenceManager:
    """Service for managing user loan preferences"""
    
    async def save_preferences(
        self,
        address: str,
        preferences: Dict[str, Any],
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Save user preferences
        
        Args:
            address: Wallet address
            preferences: Preferences dict
            session: Database session (optional)
            
        Returns:
            Saved preferences dict
        """
        try:
            from database.connection import get_session
            from database.models import UserPreferences
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._save_preferences(address, preferences, db_session)
            else:
                return await self._save_preferences(address, preferences, session)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}", exc_info=True)
            return None
    
    async def _save_preferences(
        self,
        address: str,
        preferences: Dict[str, Any],
        session
    ) -> Optional[Dict[str, Any]]:
        """Save preferences in database"""
        from database.models import UserPreferences
        from sqlalchemy import select
        from datetime import datetime
        
        try:
            # Validate preferences first
            validated = self.validate_preferences(preferences)
            if not validated['valid']:
                logger.warning(f"Invalid preferences: {validated['errors']}")
                return None
            
            # Get or create preferences
            result = await session.execute(
                select(UserPreferences).where(UserPreferences.wallet_address == address)
            )
            user_prefs = result.scalar_one_or_none()
            
            if user_prefs:
                # Update existing
                user_prefs.max_interest_rate = Decimal(str(preferences.get('max_interest_rate'))) if preferences.get('max_interest_rate') else None
                user_prefs.term_days_min = preferences.get('term_days_min')
                user_prefs.term_days_max = preferences.get('term_days_max')
                user_prefs.max_loan_amount = Decimal(str(preferences.get('max_loan_amount'))) if preferences.get('max_loan_amount') else None
                user_prefs.preferred_collateral_tokens = preferences.get('preferred_collateral_tokens', [])
                user_prefs.auto_negotiate_enabled = preferences.get('auto_negotiate_enabled', False)
                user_prefs.auto_accept_threshold = preferences.get('auto_accept_threshold', {})
                user_prefs.updated_at = datetime.utcnow()
            else:
                # Create new
                user_prefs = UserPreferences(
                    wallet_address=address,
                    max_interest_rate=Decimal(str(preferences.get('max_interest_rate'))) if preferences.get('max_interest_rate') else None,
                    term_days_min=preferences.get('term_days_min'),
                    term_days_max=preferences.get('term_days_max'),
                    max_loan_amount=Decimal(str(preferences.get('max_loan_amount'))) if preferences.get('max_loan_amount') else None,
                    preferred_collateral_tokens=preferences.get('preferred_collateral_tokens', []),
                    auto_negotiate_enabled=preferences.get('auto_negotiate_enabled', False),
                    auto_accept_threshold=preferences.get('auto_accept_threshold', {})
                )
                session.add(user_prefs)
            
            await session.commit()
            
            logger.info(f"Saved preferences for {address}")
            
            return {
                "wallet_address": address,
                "max_interest_rate": float(user_prefs.max_interest_rate) if user_prefs.max_interest_rate else None,
                "term_days_min": user_prefs.term_days_min,
                "term_days_max": user_prefs.term_days_max,
                "max_loan_amount": float(user_prefs.max_loan_amount) if user_prefs.max_loan_amount else None,
                "preferred_collateral_tokens": user_prefs.preferred_collateral_tokens or [],
                "auto_negotiate_enabled": user_prefs.auto_negotiate_enabled,
                "auto_accept_threshold": user_prefs.auto_accept_threshold or {},
            }
        except Exception as e:
            logger.error(f"Error in _save_preferences: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_preferences(
        self,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preferences
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Preferences dict or None if not found
        """
        try:
            from database.connection import get_session
            from database.models import UserPreferences
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_preferences(address, db_session)
            else:
                return await self._get_preferences(address, session)
        except Exception as e:
            logger.error(f"Error getting preferences: {e}", exc_info=True)
            return None
    
    async def _get_preferences(
        self,
        address: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get preferences from database"""
        from database.models import UserPreferences
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(UserPreferences).where(UserPreferences.wallet_address == address)
            )
            user_prefs = result.scalar_one_or_none()
            
            if not user_prefs:
                return None
            
            return {
                "wallet_address": address,
                "max_interest_rate": float(user_prefs.max_interest_rate) if user_prefs.max_interest_rate else None,
                "term_days_min": user_prefs.term_days_min,
                "term_days_max": user_prefs.term_days_max,
                "max_loan_amount": float(user_prefs.max_loan_amount) if user_prefs.max_loan_amount else None,
                "preferred_collateral_tokens": user_prefs.preferred_collateral_tokens or [],
                "auto_negotiate_enabled": user_prefs.auto_negotiate_enabled,
                "auto_accept_threshold": user_prefs.auto_accept_threshold or {},
                "created_at": user_prefs.created_at.isoformat() if user_prefs.created_at else None,
                "updated_at": user_prefs.updated_at.isoformat() if user_prefs.updated_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _get_preferences: {e}", exc_info=True)
            return None
    
    def validate_preferences(
        self,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate preference constraints
        
        Args:
            preferences: Preferences dict
            
        Returns:
            Validation result with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Validate max_interest_rate
        if 'max_interest_rate' in preferences and preferences['max_interest_rate'] is not None:
            rate = preferences['max_interest_rate']
            try:
                rate_decimal = Decimal(str(rate))
                if rate_decimal < 0 or rate_decimal > 100:
                    errors.append("max_interest_rate must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append("max_interest_rate must be a valid number")
        
        # Validate term_days_min
        if 'term_days_min' in preferences and preferences['term_days_min'] is not None:
            term_min = preferences['term_days_min']
            if not isinstance(term_min, int) or term_min <= 0:
                errors.append("term_days_min must be a positive integer")
        
        # Validate term_days_max
        if 'term_days_max' in preferences and preferences['term_days_max'] is not None:
            term_max = preferences['term_days_max']
            if not isinstance(term_max, int) or term_max <= 0:
                errors.append("term_days_max must be a positive integer")
        
        # Validate term range
        if ('term_days_min' in preferences and preferences['term_days_min'] is not None and
            'term_days_max' in preferences and preferences['term_days_max'] is not None):
            if preferences['term_days_max'] < preferences['term_days_min']:
                errors.append("term_days_max must be >= term_days_min")
        
        # Validate max_loan_amount
        if 'max_loan_amount' in preferences and preferences['max_loan_amount'] is not None:
            amount = preferences['max_loan_amount']
            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal <= 0:
                    errors.append("max_loan_amount must be positive")
            except (ValueError, TypeError):
                errors.append("max_loan_amount must be a valid number")
        
        # Validate preferred_collateral_tokens
        if 'preferred_collateral_tokens' in preferences:
            tokens = preferences['preferred_collateral_tokens']
            if not isinstance(tokens, list):
                errors.append("preferred_collateral_tokens must be a list")
            else:
                for token in tokens:
                    if not isinstance(token, str) or len(token) != 42 or not token.startswith('0x'):
                        errors.append(f"Invalid token address format: {token}")
                        break
        
        # Validate auto_accept_threshold
        if 'auto_accept_threshold' in preferences and preferences['auto_accept_threshold']:
            threshold = preferences['auto_accept_threshold']
            if not isinstance(threshold, dict):
                errors.append("auto_accept_threshold must be a dictionary")
            else:
                # Validate threshold structure
                if 'max_interest_rate' in threshold:
                    try:
                        rate = Decimal(str(threshold['max_interest_rate']))
                        if rate < 0 or rate > 100:
                            errors.append("auto_accept_threshold.max_interest_rate must be between 0 and 100")
                    except (ValueError, TypeError):
                        errors.append("auto_accept_threshold.max_interest_rate must be a valid number")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

