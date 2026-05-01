"""
KYC integration service for identity verification
"""
from typing import Dict, Optional, Any, List
from utils.logger import get_logger
from database.connection import get_session
from database.models import IdentityVerification
from sqlalchemy import select
from datetime import datetime, timedelta

logger = get_logger(__name__)


class KYCService:
    """Service for integrating with KYC providers"""
    
    # Available KYC providers
    PROVIDERS = {
        'sumsub': {
            'name': 'Sumsub',
            'enabled': True,
        },
        'onfido': {
            'name': 'Onfido',
            'enabled': True,
        },
        'jumio': {
            'name': 'Jumio',
            'enabled': True,
        },
    }
    
    # Score boosts
    KYC_BOOST = 50  # Standard KYC verification
    ENHANCED_KYC_BOOST = 75  # Enhanced KYC with additional checks
    
    def __init__(self):
        # Initialize provider clients (would be configured with API keys in production)
        self.sumsub_api_key = None  # Would load from env
        self.onfido_api_key = None
        self.jumio_api_key = None
    
    async def initiate_kyc(
        self,
        address: str,
        provider: str = 'sumsub',
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate KYC verification with provider
        
        Args:
            address: Wallet address
            provider: KYC provider ('sumsub', 'onfido', 'jumio')
            session: Database session (optional)
            
        Returns:
            Verification initiation result dict
        """
        try:
            if provider not in self.PROVIDERS:
                logger.warning(f"Unknown KYC provider: {provider}")
                return None
            
            if not self.PROVIDERS[provider]['enabled']:
                logger.warning(f"KYC provider {provider} is not enabled")
                return None
            
            # Check if verification already exists
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._initiate_kyc(address, provider, db_session)
            else:
                return await self._initiate_kyc(address, provider, session)
        except Exception as e:
            logger.error(f"Error initiating KYC: {e}", exc_info=True)
            return None
    
    async def _initiate_kyc(
        self,
        address: str,
        provider: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Initiate KYC verification"""
        try:
            # Check existing verification
            result = await session.execute(
                select(IdentityVerification).where(
                    IdentityVerification.wallet_address == address,
                    IdentityVerification.verification_type == 'kyc',
                    IdentityVerification.provider == provider
                ).order_by(IdentityVerification.created_at.desc())
            )
            existing = result.scalar_one_or_none()
            
            if existing and existing.status == 'verified':
                # Check if expired
                if existing.expires_at and existing.expires_at > datetime.utcnow():
                    return {
                        "address": address,
                        "provider": provider,
                        "status": "already_verified",
                        "verification_id": existing.id,
                    }
            
            # Create verification record
            verification = IdentityVerification(
                wallet_address=address,
                verification_type='kyc',
                provider=provider,
                status='pending',
                verification_data={}
            )
            session.add(verification)
            await session.flush()
            
            # In production, would call provider API to initiate verification
            # For now, simulate initiation
            verification_url = f"https://{provider}.com/verify/{verification.id}"
            
            verification.verification_data = {
                "verification_url": verification_url,
                "initiated_at": datetime.utcnow().isoformat(),
            }
            
            await session.commit()
            
            logger.info(f"Initiated KYC verification for {address} with {provider}")
            
            return {
                "address": address,
                "provider": provider,
                "verification_id": verification.id,
                "verification_url": verification_url,
                "status": "pending",
            }
        except Exception as e:
            logger.error(f"Error in _initiate_kyc: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def verify_kyc_status(
        self,
        address: str,
        provider: Optional[str] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Check KYC verification status
        
        Args:
            address: Wallet address
            provider: Optional provider filter
            session: Database session (optional)
            
        Returns:
            KYC status dict
        """
        try:
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._verify_kyc_status(address, provider, db_session)
            else:
                return await self._verify_kyc_status(address, provider, session)
        except Exception as e:
            logger.error(f"Error verifying KYC status: {e}", exc_info=True)
            return None
    
    async def _verify_kyc_status(
        self,
        address: str,
        provider: Optional[str],
        session
    ) -> Optional[Dict[str, Any]]:
        """Get KYC status from database"""
        try:
            query = select(IdentityVerification).where(
                IdentityVerification.wallet_address == address,
                IdentityVerification.verification_type == 'kyc'
            )
            
            if provider:
                query = query.where(IdentityVerification.provider == provider)
            
            query = query.order_by(IdentityVerification.created_at.desc())
            
            result = await session.execute(query)
            verifications = result.scalars().all()
            
            if not verifications:
                return {
                    "address": address,
                    "verified": False,
                    "status": "not_initiated",
                }
            
            latest = verifications[0]
            
            return {
                "address": address,
                "verified": latest.status == 'verified',
                "status": latest.status,
                "provider": latest.provider,
                "verified_at": latest.verified_at.isoformat() if latest.verified_at else None,
                "expires_at": latest.expires_at.isoformat() if latest.expires_at else None,
                "score_boost": latest.score_boost or 0,
            }
        except Exception as e:
            logger.error(f"Error in _verify_kyc_status: {e}", exc_info=True)
            return None
    
    def get_kyc_providers(self) -> List[Dict[str, Any]]:
        """
        List available KYC providers
        
        Returns:
            List of provider dicts
        """
        return [
            {
                "id": provider_id,
                "name": provider_info['name'],
                "enabled": provider_info['enabled'],
            }
            for provider_id, provider_info in self.PROVIDERS.items()
        ]
    
    async def calculate_kyc_boost(
        self,
        address: str,
        session=None
    ) -> int:
        """
        Calculate score boost from KYC verification
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Score boost points
        """
        try:
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_kyc_boost(address, db_session)
            else:
                return await self._calculate_kyc_boost(address, session)
        except Exception as e:
            logger.error(f"Error calculating KYC boost: {e}", exc_info=True)
            return 0
    
    async def _calculate_kyc_boost(
        self,
        address: str,
        session
    ) -> int:
        """Calculate KYC boost from database"""
        try:
            result = await session.execute(
                select(IdentityVerification).where(
                    IdentityVerification.wallet_address == address,
                    IdentityVerification.verification_type == 'kyc',
                    IdentityVerification.status == 'verified'
                ).order_by(IdentityVerification.verified_at.desc())
            )
            verification = result.scalar_one_or_none()
            
            if not verification:
                return 0
            
            # Check if expired
            if verification.expires_at and verification.expires_at < datetime.utcnow():
                return 0
            
            # Check if enhanced KYC
            verification_data = verification.verification_data or {}
            is_enhanced = verification_data.get('enhanced', False)
            
            return self.ENHANCED_KYC_BOOST if is_enhanced else self.KYC_BOOST
        except Exception as e:
            logger.error(f"Error in _calculate_kyc_boost: {e}", exc_info=True)
            return 0
    
    async def update_kyc_status(
        self,
        verification_id: int,
        status: str,
        verification_data: Optional[Dict[str, Any]] = None,
        session=None
    ) -> bool:
        """
        Update KYC verification status (typically called via webhook)
        
        Args:
            verification_id: Verification ID
            status: New status ('verified', 'rejected', 'expired')
            verification_data: Optional additional data
            session: Database session (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._update_kyc_status(verification_id, status, verification_data, db_session)
            else:
                return await self._update_kyc_status(verification_id, status, verification_data, session)
        except Exception as e:
            logger.error(f"Error updating KYC status: {e}", exc_info=True)
            return False
    
    async def _update_kyc_status(
        self,
        verification_id: int,
        status: str,
        verification_data: Optional[Dict[str, Any]],
        session
    ) -> bool:
        """Update KYC status in database"""
        try:
            result = await session.execute(
                select(IdentityVerification).where(IdentityVerification.id == verification_id)
            )
            verification = result.scalar_one_or_none()
            
            if not verification:
                return False
            
            verification.status = status
            verification.updated_at = datetime.utcnow()
            
            if status == 'verified':
                verification.verified_at = datetime.utcnow()
                # Set expiration (e.g., 1 year)
                verification.expires_at = datetime.utcnow() + timedelta(days=365)
                
                # Calculate boost
                is_enhanced = (verification_data or {}).get('enhanced', False) if verification_data else False
                verification.score_boost = self.ENHANCED_KYC_BOOST if is_enhanced else self.KYC_BOOST
            
            if verification_data:
                existing_data = verification.verification_data or {}
                existing_data.update(verification_data)
                verification.verification_data = existing_data
            
            await session.commit()
            
            logger.info(f"Updated KYC verification {verification_id} to status {status}")
            return True
        except Exception as e:
            logger.error(f"Error in _update_kyc_status: {e}", exc_info=True)
            await session.rollback()
            return False

