"""
Portfolio service for analyzing user token holdings, transactions, and DeFi activity
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioService:
    """Service for portfolio analysis and insights"""
    
    # Known DeFi protocol addresses (can be expanded)
    DEFI_PROTOCOLS = {
        # Add known DeFi protocol addresses here
        # Example: "0x1234...": "Uniswap",
    }
    
    @staticmethod
    async def get_token_holdings(
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get token holdings breakdown for an address
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of token holdings with balances and USD values
        """
        try:
            from database.connection import get_session
            from database.repositories import TransactionRepository, TokenTransfer
            
            if session is None:
                async with get_session() as db_session:
                    return await PortfolioService._calculate_holdings(address, db_session)
            else:
                return await PortfolioService._calculate_holdings(address, session)
        except Exception as e:
            logger.error(f"Error getting token holdings: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def _calculate_holdings(address: str, session) -> List[Dict[str, Any]]:
        """Calculate token holdings from token transfers"""
        from database.models import TokenTransfer
        from sqlalchemy import select, func
        
        try:
            # Get all token transfers for this address
            result = await session.execute(
                select(TokenTransfer)
                .where(
                    (TokenTransfer.from_address == address) |
                    (TokenTransfer.to_address == address)
                )
            )
            transfers = result.scalars().all()
            
            # Aggregate balances by token
            balances = defaultdict(lambda: {"in": Decimal("0"), "out": Decimal("0")})
            
            for transfer in transfers:
                token_addr = transfer.token_address
                amount = Decimal(str(transfer.amount)) if transfer.amount else Decimal("0")
                
                if transfer.from_address and transfer.from_address.lower() == address.lower():
                    balances[token_addr]["out"] += amount
                if transfer.to_address and transfer.to_address.lower() == address.lower():
                    balances[token_addr]["in"] += amount
            
            # Calculate net balances
            holdings = []
            total_value = Decimal("0")
            
            for token_addr, balance_data in balances.items():
                net_balance = balance_data["in"] - balance_data["out"]
                if net_balance > 0:
                    # Convert from wei (assuming 18 decimals)
                    balance_display = float(net_balance) / 1e18
                    
                    # TODO: Get USD value from oracle/price feed
                    usd_value = balance_display * 1.0  # Placeholder
                    total_value += Decimal(str(usd_value))
                    
                    holdings.append({
                        "token_address": token_addr,
                        "balance": balance_display,
                        "balance_raw": str(net_balance),
                        "usd_value": float(usd_value),
                        "percentage": 0.0,  # Will be calculated after total
                    })
            
            # Calculate percentages
            if total_value > 0:
                for holding in holdings:
                    holding["percentage"] = (holding["usd_value"] / float(total_value)) * 100
            
            # Sort by USD value descending
            holdings.sort(key=lambda x: x["usd_value"], reverse=True)
            
            return holdings
        except Exception as e:
            logger.error(f"Error calculating holdings: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_transaction_summary(
        address: str,
        timeframe_days: int = 30,
        session=None
    ) -> Dict[str, Any]:
        """
        Get transaction summary for an address
        
        Args:
            address: Wallet address
            timeframe_days: Number of days to analyze
            session: Database session (optional)
            
        Returns:
            Transaction summary dictionary
        """
        try:
            from database.connection import get_session
            from database.models import Transaction
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            if session is None:
                async with get_session() as db_session:
                    return await PortfolioService._calculate_summary(address, timeframe_days, db_session)
            else:
                return await PortfolioService._calculate_summary(address, timeframe_days, session)
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}", exc_info=True)
            return {}
    
    @staticmethod
    async def _calculate_summary(address: str, timeframe_days: int, session) -> Dict[str, Any]:
        """Calculate transaction summary"""
        from database.models import Transaction
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta
        
        try:
            start_date = datetime.utcnow() - timedelta(days=timeframe_days)
            
            # Get transactions in timeframe
            result = await session.execute(
                select(Transaction)
                .where(
                    and_(
                        Transaction.wallet_address == address,
                        Transaction.block_timestamp >= start_date
                    )
                )
            )
            transactions = result.scalars().all()
            
            # Calculate statistics
            total_txs = len(transactions)
            total_volume = Decimal("0")
            total_gas = 0
            tx_types = defaultdict(int)
            
            for tx in transactions:
                if tx.value:
                    total_volume += Decimal(str(tx.value))
                if tx.gas_used:
                    total_gas += tx.gas_used
                tx_types[tx.tx_type] += 1
            
            return {
                "total_transactions": total_txs,
                "total_volume": float(total_volume) / 1e18,  # Convert from wei
                "total_gas_used": total_gas,
                "average_gas_per_tx": total_gas / total_txs if total_txs > 0 else 0,
                "transaction_types": dict(tx_types),
                "timeframe_days": timeframe_days,
                "start_date": start_date.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating summary: {e}", exc_info=True)
            return {}
    
    @staticmethod
    async def get_defi_activity(
        address: str,
        session=None
    ) -> Dict[str, Any]:
        """
        Get DeFi activity summary
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            DeFi activity summary
        """
        try:
            from database.connection import get_session
            from database.models import Transaction
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await PortfolioService._analyze_defi_activity(address, db_session)
            else:
                return await PortfolioService._analyze_defi_activity(address, session)
        except Exception as e:
            logger.error(f"Error getting DeFi activity: {e}", exc_info=True)
            return {}
    
    @staticmethod
    async def _analyze_defi_activity(address: str, session) -> Dict[str, Any]:
        """Analyze DeFi protocol interactions"""
        from database.models import Transaction
        from sqlalchemy import select
        from collections import defaultdict
        
        try:
            # Get contract interactions
            result = await session.execute(
                select(Transaction)
                .where(
                    Transaction.wallet_address == address,
                    Transaction.contract_address.isnot(None)
                )
            )
            transactions = result.scalars().all()
            
            # Group by protocol/contract
            protocol_activity = defaultdict(lambda: {"count": 0, "volume": Decimal("0")})
            
            for tx in transactions:
                contract = tx.contract_address
                protocol_name = PortfolioService.DEFI_PROTOCOLS.get(contract, f"Contract {contract[:10]}...")
                
                protocol_activity[protocol_name]["count"] += 1
                if tx.value:
                    protocol_activity[protocol_name]["volume"] += Decimal(str(tx.value))
            
            # Convert to list format
            protocols = []
            for protocol, data in protocol_activity.items():
                protocols.append({
                    "protocol": protocol,
                    "contract_address": next(
                        (addr for addr, name in PortfolioService.DEFI_PROTOCOLS.items() if name == protocol),
                        None
                    ),
                    "interaction_count": data["count"],
                    "total_volume": float(data["volume"]) / 1e18,
                })
            
            protocols.sort(key=lambda x: x["total_volume"], reverse=True)
            
            return {
                "protocols": protocols,
                "total_protocols": len(protocols),
                "total_interactions": sum(p["interaction_count"] for p in protocols),
                "total_volume": sum(p["total_volume"] for p in protocols),
            }
        except Exception as e:
            logger.error(f"Error analyzing DeFi activity: {e}", exc_info=True)
            return {}
    
    @staticmethod
    async def assess_portfolio_risk(
        address: str,
        session=None
    ) -> Dict[str, Any]:
        """
        Assess portfolio risk
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Risk assessment dictionary
        """
        try:
            # Get holdings and activity
            holdings = await PortfolioService.get_token_holdings(address, session)
            summary = await PortfolioService.get_transaction_summary(address, 30, session)
            defi_activity = await PortfolioService.get_defi_activity(address, session)
            
            # Calculate risk factors
            risk_factors = []
            risk_score = 0  # 0-100, higher = riskier
            
            # Concentration risk
            if holdings:
                top_holding_pct = holdings[0]["percentage"] if holdings else 0
                if top_holding_pct > 80:
                    risk_score += 30
                    risk_factors.append({
                        "factor": "High concentration",
                        "severity": "high",
                        "description": f"Top holding represents {top_holding_pct:.1f}% of portfolio"
                    })
                elif top_holding_pct > 50:
                    risk_score += 15
                    risk_factors.append({
                        "factor": "Moderate concentration",
                        "severity": "medium",
                        "description": f"Top holding represents {top_holding_pct:.1f}% of portfolio"
                    })
            
            # Transaction volume risk
            if summary.get("total_transactions", 0) > 1000:
                risk_score += 10
                risk_factors.append({
                    "factor": "High transaction volume",
                    "severity": "medium",
                    "description": "Very high number of transactions may indicate bot activity"
                })
            
            # DeFi interaction risk
            if defi_activity.get("total_protocols", 0) > 10:
                risk_score += 5
                risk_factors.append({
                    "factor": "Multiple DeFi protocols",
                    "severity": "low",
                    "description": "Interacting with many protocols increases smart contract risk"
                })
            
            # Determine risk level
            if risk_score >= 40:
                risk_level = "high"
            elif risk_score >= 20:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Generate recommendations
            recommendations = []
            if top_holding_pct > 50:
                recommendations.append("Consider diversifying your portfolio to reduce concentration risk")
            if summary.get("total_transactions", 0) > 1000:
                recommendations.append("Monitor transaction patterns for unusual activity")
            if not recommendations:
                recommendations.append("Portfolio risk is well-managed")
            
            return {
                "risk_score": min(100, risk_score),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_date": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}", exc_info=True)
            return {
                "risk_score": 0,
                "risk_level": "unknown",
                "risk_factors": [],
                "recommendations": ["Unable to assess risk at this time"],
            }

