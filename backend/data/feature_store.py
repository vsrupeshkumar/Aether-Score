"""
Feature Store

Storage and retrieval of computed features for ML training and inference.
"""

import os
import json
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database.models import UserData
from database.connection import get_db_session
from utils.logger import get_logger
from utils.cache import cache_get, cache_set

logger = get_logger(__name__)


class FeatureStore:
    """Store and retrieve computed features"""
    
    def __init__(self):
        self.cache_ttl = int(os.getenv("FEATURE_CACHE_TTL", "3600"))  # 1 hour
        self.store_dir = Path(os.getenv("FEATURE_STORE_DIR", "backend/data/feature_store"))
        self.store_dir.mkdir(parents=True, exist_ok=True)
    
    async def store_features(self, address: str, features: Dict[str, Any], version: str = "latest") -> bool:
        """
        Store features for an address
        
        Args:
            address: Wallet address
            features: Feature dictionary
            version: Feature version identifier
            
        Returns:
            Success status
        """
        try:
            # Store in database
            async with get_db_session() as session:
                # Store as JSON in user_data table
                feature_key = f"features_{version}"
                
                from database.repositories import UserDataRepository
                await UserDataRepository.upsert_user_data(
                    session,
                    address,
                    feature_key,
                    json.dumps(features)
                )
                
                await session.commit()
            
            # Store in cache
            cache_key = f"features:{address}:{version}"
            cache_set(cache_key, features, ttl=self.cache_ttl)
            
            # Store in file system (optional, for backup)
            feature_file = self.store_dir / f"{address}_{version}.json"
            with open(feature_file, "w") as f:
                json.dump({
                    "address": address,
                    "version": version,
                    "features": features,
                    "stored_at": datetime.now().isoformat(),
                }, f, indent=2)
            
            logger.debug(f"Stored features for {address}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing features: {e}", exc_info=True)
            return False
    
    async def get_features(self, address: str, version: str = "latest") -> Optional[Dict[str, Any]]:
        """
        Retrieve features for an address
        
        Args:
            address: Wallet address
            version: Feature version identifier
            
        Returns:
            Feature dictionary or None
        """
        try:
            # Try cache first
            cache_key = f"features:{address}:{version}"
            cached = cache_get(cache_key)
            if cached:
                return cached
            
            # Try database
            async with get_db_session() as session:
                feature_key = f"features_{version}"
                
                from database.repositories import UserDataRepository
                user_data = await UserDataRepository.get_user_data(session, address)
                
                if user_data and user_data.data_key == feature_key:
                    features = json.loads(user_data.data_value)
                    # Cache for future use
                    cache_set(cache_key, features, ttl=self.cache_ttl)
                    return features
            
            # Try file system
            feature_file = self.store_dir / f"{address}_{version}.json"
            if feature_file.exists():
                with open(feature_file, "r") as f:
                    data = json.load(f)
                    features = data.get("features")
                    if features:
                        cache_set(cache_key, features, ttl=self.cache_ttl)
                        return features
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving features: {e}", exc_info=True)
            return None
    
    async def get_batch_features(self, addresses: List[str], version: str = "latest") -> Dict[str, Dict[str, Any]]:
        """Get features for multiple addresses"""
        results = {}
        
        for address in addresses:
            features = await self.get_features(address, version)
            if features:
                results[address] = features
        
        return results
    
    async def list_stored_addresses(self, version: str = "latest") -> List[str]:
        """List all addresses with stored features"""
        try:
            async with get_db_session() as session:
                feature_key = f"features_{version}"
                stmt = select(UserData).where(UserData.data_key == feature_key)
                result = await session.execute(stmt)
                user_data_list = result.scalars().all()
                
                return [ud.wallet_address for ud in user_data_list]
        except Exception as e:
            logger.error(f"Error listing stored addresses: {e}", exc_info=True)
            return []

