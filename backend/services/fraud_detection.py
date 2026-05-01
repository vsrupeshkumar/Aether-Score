"""
Fraud Detection Service

Detects Sybil attacks, suspicious patterns, and behavioral anomalies.
"""

import os
from typing import Dict, List, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import networkx as nx

from database.models import Transaction, TokenTransfer, User
from database.connection import get_db_session
from services.feature_engineering import FeatureEngineering
from utils.logger import get_logger

logger = get_logger(__name__)


class FraudDetectionService:
    """Service for detecting fraud and suspicious activity"""
    
    def __init__(self):
        self.feature_engineering = FeatureEngineering()
        self.sybil_threshold = float(os.getenv("SYBIL_THRESHOLD", "0.7"))
        self.anomaly_threshold = float(os.getenv("ANOMALY_THRESHOLD", "0.8"))
    
    async def check_fraud_risk(self, address: str) -> Dict[str, Any]:
        """
        Check fraud risk for an address
        
        Returns:
            Dict with fraud risk score and indicators
        """
        try:
            # Extract features
            features = await self.feature_engineering.extract_all_features(address)
            
            # Check various fraud indicators
            sybil_score = await self._detect_sybil(address, features)
            pattern_score = await self._detect_suspicious_patterns(address, features)
            anomaly_score = await self._detect_behavioral_anomalies(address, features)
            
            # Calculate overall fraud risk (0-100)
            fraud_risk = (
                sybil_score * 0.4 +
                pattern_score * 0.3 +
                anomaly_score * 0.3
            ) * 100
            
            # Determine risk level
            if fraud_risk >= 70:
                risk_level = "high"
            elif fraud_risk >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            indicators = []
            if sybil_score > 0.5:
                indicators.append("sybil_attack")
            if pattern_score > 0.5:
                indicators.append("suspicious_patterns")
            if anomaly_score > 0.5:
                indicators.append("behavioral_anomaly")
            
            return {
                "address": address,
                "fraud_risk": fraud_risk,
                "risk_level": risk_level,
                "sybil_score": sybil_score * 100,
                "pattern_score": pattern_score * 100,
                "anomaly_score": anomaly_score * 100,
                "indicators": indicators,
                "flagged": fraud_risk >= 70,
            }
            
        except Exception as e:
            logger.error(f"Error checking fraud risk: {e}", exc_info=True)
            return {
                "address": address,
                "fraud_risk": 0,
                "risk_level": "unknown",
                "error": str(e),
            }
    
    async def _detect_sybil(self, address: str, features: Dict[str, Any]) -> float:
        """
        Detect Sybil attack patterns
        
        Returns:
            Sybil risk score (0-1)
        """
        try:
            async with get_db_session() as session:
                # Get transactions
                stmt = select(Transaction).where(
                    Transaction.wallet_address == address
                )
                result = await session.execute(stmt)
                transactions = list(result.scalars().all())
                
                if len(transactions) < 5:
                    return 0.0  # Not enough data
                
                # Check for funding patterns (same source addresses)
                from_addresses = [t.from_address for t in transactions if t.from_address]
                from_address_counts = Counter(from_addresses)
                
                # If most transactions come from a few addresses, suspicious
                if len(from_address_counts) > 0:
                    top_sources = from_address_counts.most_common(3)
                    top_source_ratio = sum(count for _, count in top_sources) / len(transactions)
                    
                    if top_source_ratio > 0.8:
                        return 0.8  # High Sybil risk
                
                # Check for rapid account creation and funding
                if transactions:
                    first_tx = min(t.block_timestamp for t in transactions if t.block_timestamp)
                    recent_txs = [
                        t for t in transactions
                        if t.block_timestamp and (t.block_timestamp - first_tx).days < 1
                    ]
                    
                    if len(recent_txs) > 10:
                        return 0.7  # Suspicious rapid activity
                
                # Check address clustering
                clustering_score = features.get("address_clustering_score", 0.0)
                if clustering_score > 0.8:
                    return 0.6  # High clustering
                
                # Check transaction graph for Sybil patterns
                graph_score = await self._analyze_transaction_graph(address, transactions)
                
                return max(0.0, min(1.0, graph_score))
                
        except Exception as e:
            logger.warning(f"Error in Sybil detection: {e}")
            return 0.0
    
    async def _analyze_transaction_graph(
        self,
        address: str,
        transactions: List[Transaction]
    ) -> float:
        """Analyze transaction graph for Sybil patterns"""
        try:
            # Build graph
            G = nx.DiGraph()
            
            for tx in transactions:
                if tx.from_address and tx.to_address:
                    from_addr = tx.from_address.lower()
                    to_addr = tx.to_address.lower()
                    
                    if G.has_edge(from_addr, to_addr):
                        G[from_addr][to_addr]['weight'] += 1
                    else:
                        G.add_edge(from_addr, to_addr, weight=1)
            
            if len(G.nodes()) < 3:
                return 0.0
            
            # Check for star patterns (many addresses connected to one)
            in_degrees = dict(G.in_degree())
            out_degrees = dict(G.out_degree())
            
            # If address has many incoming connections from different sources
            if address.lower() in in_degrees:
                if in_degrees[address.lower()] > 10:
                    return 0.7
            
            # Check for bipartite patterns (common in Sybil attacks)
            # Simplified check: many addresses with similar connection patterns
            if len(G.nodes()) > 5:
                # Calculate clustering coefficient
                try:
                    clustering = nx.average_clustering(G.to_undirected())
                    if clustering > 0.5:
                        return 0.6
                except:
                    pass
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error analyzing transaction graph: {e}")
            return 0.0
    
    async def _detect_suspicious_patterns(
        self,
        address: str,
        features: Dict[str, Any]
    ) -> float:
        """Detect suspicious transaction patterns"""
        try:
            score = 0.0
            
            # Check for unusual transaction frequency
            tx_frequency = features.get("tx_frequency_daily", 0.0)
            if tx_frequency > 100:  # Very high frequency
                score += 0.3
            
            # Check for low transaction regularity
            regularity = features.get("tx_regularity_score", 0.5)
            if regularity < 0.2:  # Very irregular
                score += 0.2
            
            # Check for high failure rate
            failure_rate = features.get("tx_failure_rate", 0.0)
            if failure_rate > 0.3:  # High failure rate
                score += 0.3
            
            # Check for rapid score changes (if available)
            # This would require score history
            
            # Check for unusual token concentration
            token_concentration = features.get("token_concentration", 0.5)
            if token_concentration > 0.9:  # Very concentrated
                score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"Error detecting suspicious patterns: {e}")
            return 0.0
    
    async def _detect_behavioral_anomalies(
        self,
        address: str,
        features: Dict[str, Any]
    ) -> float:
        """Detect behavioral anomalies"""
        try:
            score = 0.0
            
            # Check for unusual time patterns
            time_variance = features.get("tx_time_of_day_variance", 0.0)
            if time_variance < 10:  # Very consistent timing (bot-like)
                score += 0.3
            
            # Check for low activity consistency
            consistency = features.get("activity_consistency", 0.5)
            if consistency < 0.2:  # Very inconsistent
                score += 0.2
            
            # Check for unusual gas usage
            gas_efficiency = features.get("tx_gas_efficiency", 0.5)
            if gas_efficiency < 0.2:  # Very inefficient
                score += 0.2
            
            # Check for low account age with high activity
            account_age = features.get("account_age_days", 0)
            tx_count = features.get("tx_count", 0)
            
            if account_age < 7 and tx_count > 50:
                score += 0.3  # New account with high activity
            
            return min(1.0, score)
            
        except Exception as e:
            logger.warning(f"Error detecting behavioral anomalies: {e}")
            return 0.0
    
    async def batch_check_fraud(self, addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check fraud risk for multiple addresses"""
        results = {}
        
        for address in addresses:
            result = await self.check_fraud_risk(address)
            results[address] = result
        
        return results

