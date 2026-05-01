"""
Loan service for managing loans, calculating schedules, and comparing loans
"""
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from utils.logger import get_logger
from config.network import get_network_config, get_healthy_rpc_urls

load_dotenv()

logger = get_logger(__name__)


class LoanService:
    """Service for loan management and calculations"""
    
    def __init__(self):
        # Use centralized network configuration
        self.network_config = get_network_config()
        healthy_rpcs = get_healthy_rpc_urls(self.network_config)
        self.rpc_url = healthy_rpcs[0] if healthy_rpcs else self.network_config.get_primary_rpc()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.lending_vault_address = os.getenv("LENDING_VAULT_ADDRESS")
        
        # Load LendingVault ABI
        self.contract_abi = self._load_contract_abi()
        if self.lending_vault_address and self.contract_abi:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.lending_vault_address),
                abi=self.contract_abi
            )
        else:
            self.contract = None
            logger.warning("LendingVault contract not configured")
    
    def _load_contract_abi(self) -> Optional[List]:
        """Load LendingVault contract ABI"""
        try:
            import json
            from pathlib import Path
            
            abi_path = Path(__file__).parent.parent / "abis" / "LendingVaultV2.json"
            if abi_path.exists():
                with open(abi_path, 'r') as f:
                    abi_data = json.load(f)
                    if isinstance(abi_data, list):
                        return abi_data
                    elif isinstance(abi_data, dict) and "abi" in abi_data:
                        return abi_data["abi"]
        except Exception as e:
            logger.error(f"Failed to load LendingVault ABI: {e}")
        return None
    
    async def get_user_loans(self, address: str, from_db: bool = True) -> List[Dict[str, Any]]:
        """
        Get all loans for a user
        
        Args:
            address: User wallet address
            from_db: Whether to fetch from database (True) or blockchain (False)
            
        Returns:
            List of loan dictionaries
        """
        if from_db:
            # Fetch from database
            try:
                from database.connection import get_session
                from database.repositories import LoanRepository
                
                async with get_session() as session:
                    loans = await LoanRepository.get_user_loans(session, address)
                    return [self._loan_to_dict(loan) for loan in loans]
            except Exception as e:
                logger.error(f"Error fetching loans from database: {e}")
                # Fallback to blockchain
                return await self.sync_loans_from_blockchain(address)
        else:
            # Fetch from blockchain
            return await self.sync_loans_from_blockchain(address)
    
    async def sync_loans_from_blockchain(self, address: str) -> List[Dict[str, Any]]:
        """
        Sync loans from blockchain (LendingVault contract)
        
        Args:
            address: User wallet address
            
        Returns:
            List of loan dictionaries
        """
        if not self.contract:
            logger.warning("Cannot sync loans: LendingVault contract not configured")
            return []
        
        try:
            # Get borrower loans from contract
            loan_ids = self.contract.functions.getBorrowerLoans(address).call()
            
            loans = []
            for loan_id in loan_ids:
                try:
                    # Get loan details (this depends on contract structure)
                    # For now, we'll create a basic structure
                    total_owed = self.contract.functions.calculateTotalOwed(loan_id).call()
                    
                    loan_data = {
                        "loan_id": int(loan_id),
                        "wallet_address": address,
                        "total_owed": float(total_owed) / 1e18,  # Convert from wei
                        "status": "active",  # Default status
                        "source": "blockchain",
                    }
                    loans.append(loan_data)
                except Exception as e:
                    logger.error(f"Error fetching loan {loan_id}: {e}")
                    continue
            
            return loans
        except Exception as e:
            logger.error(f"Error syncing loans from blockchain: {e}")
            return []
    
    def calculate_repayment_schedule(
        self,
        loan_amount: float,
        interest_rate: float,
        term_days: int,
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate repayment schedule for a loan
        
        Args:
            loan_amount: Principal loan amount
            interest_rate: Annual interest rate (as percentage, e.g., 7.5 for 7.5%)
            term_days: Loan term in days
            start_date: Loan start date (defaults to now)
            
        Returns:
            List of payment schedule entries
        """
        if start_date is None:
            start_date = datetime.now()
        
        # Convert interest rate to decimal
        annual_rate = Decimal(str(interest_rate)) / Decimal("100")
        daily_rate = annual_rate / Decimal("365")
        
        # Calculate total interest
        total_interest = Decimal(str(loan_amount)) * daily_rate * Decimal(str(term_days))
        total_amount = Decimal(str(loan_amount)) + total_interest
        
        # Calculate daily payment
        daily_payment = total_amount / Decimal(str(term_days))
        
        schedule = []
        remaining_principal = Decimal(str(loan_amount))
        payment_date = start_date
        
        for day in range(1, term_days + 1):
            # Calculate interest for this period
            period_interest = remaining_principal * daily_rate
            
            # Calculate principal payment
            period_principal = daily_payment - period_interest
            
            # Update remaining principal
            remaining_principal = max(Decimal("0"), remaining_principal - period_principal)
            
            payment_date = start_date + timedelta(days=day)
            
            schedule.append({
                "payment_number": day,
                "payment_date": payment_date.isoformat(),
                "principal": float(period_principal),
                "interest": float(period_interest),
                "total_payment": float(daily_payment),
                "remaining_principal": float(remaining_principal),
            })
        
        return schedule
    
    def calculate_early_repayment_savings(
        self,
        loan_amount: float,
        interest_rate: float,
        term_days: int,
        early_payment_date: datetime,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate savings from early loan repayment
        
        Args:
            loan_amount: Principal loan amount
            interest_rate: Annual interest rate (as percentage)
            term_days: Original loan term in days
            early_payment_date: Date of early repayment
            start_date: Loan start date (defaults to now)
            
        Returns:
            Dict with savings calculation details
        """
        if start_date is None:
            start_date = datetime.now()
        
        if early_payment_date <= start_date:
            return {
                "savings": 0.0,
                "interest_saved": 0.0,
                "days_saved": 0,
                "original_total": 0.0,
                "early_total": 0.0,
            }
        
        # Calculate original total payment
        annual_rate = Decimal(str(interest_rate)) / Decimal("100")
        daily_rate = annual_rate / Decimal("365")
        original_total_interest = Decimal(str(loan_amount)) * daily_rate * Decimal(str(term_days))
        original_total = Decimal(str(loan_amount)) + original_total_interest
        
        # Calculate days until early payment
        days_elapsed = (early_payment_date - start_date).days
        days_saved = term_days - days_elapsed
        
        if days_saved <= 0:
            return {
                "savings": 0.0,
                "interest_saved": 0.0,
                "days_saved": 0,
                "original_total": float(original_total),
                "early_total": float(original_total),
            }
        
        # Calculate interest paid until early payment
        early_interest = Decimal(str(loan_amount)) * daily_rate * Decimal(str(days_elapsed))
        early_total = Decimal(str(loan_amount)) + early_interest
        
        # Calculate savings
        interest_saved = original_total_interest - early_interest
        total_savings = original_total - early_total
        
        return {
            "savings": float(total_savings),
            "interest_saved": float(interest_saved),
            "days_saved": days_saved,
            "original_total": float(original_total),
            "early_total": float(early_total),
            "original_interest": float(original_total_interest),
            "early_interest": float(early_interest),
        }
    
    def compare_loans(self, loan1: Dict[str, Any], loan2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two loan offers
        
        Args:
            loan1: First loan offer
            loan2: Second loan offer
            
        Returns:
            Comparison results
        """
        # Extract loan details
        amount1 = float(loan1.get("amount", 0))
        rate1 = float(loan1.get("interestRate", 0)) / 100  # Convert from basis points or percentage
        term1 = int(loan1.get("duration", 0)) // (24 * 60 * 60)  # Convert seconds to days
        
        amount2 = float(loan2.get("amount", 0))
        rate2 = float(loan2.get("interestRate", 0)) / 100
        term2 = int(loan2.get("duration", 0)) // (24 * 60 * 60)
        
        # Calculate totals
        total1 = self._calculate_total_cost(amount1, rate1, term1)
        total2 = self._calculate_total_cost(amount2, rate2, term2)
        
        # Calculate monthly payments (approximate)
        monthly1 = total1 / (term1 / 30) if term1 > 0 else 0
        monthly2 = total2 / (term2 / 30) if term2 > 0 else 0
        
        # Determine better loan
        better_loan = "loan1" if total1 < total2 else "loan2" if total2 < total1 else "equal"
        
        return {
            "loan1": {
                "amount": amount1,
                "interest_rate": rate1 * 100,
                "term_days": term1,
                "total_cost": total1,
                "monthly_payment": monthly1,
            },
            "loan2": {
                "amount": amount2,
                "interest_rate": rate2 * 100,
                "term_days": term2,
                "total_cost": total2,
                "monthly_payment": monthly2,
            },
            "comparison": {
                "better_loan": better_loan,
                "cost_difference": abs(total1 - total2),
                "rate_difference": abs(rate1 - rate2) * 100,
                "term_difference": abs(term1 - term2),
            },
        }
    
    def _calculate_total_cost(self, amount: float, rate: float, term_days: int) -> float:
        """Calculate total cost of a loan"""
        if term_days <= 0:
            return amount
        
        annual_rate = Decimal(str(rate))
        daily_rate = annual_rate / Decimal("365")
        total_interest = Decimal(str(amount)) * daily_rate * Decimal(str(term_days))
        return float(Decimal(str(amount)) + total_interest)
    
    def _loan_to_dict(self, loan) -> Dict[str, Any]:
        """Convert database loan model to dictionary"""
        return {
            "id": loan.id,
            "loan_id": loan.loan_id,
            "wallet_address": loan.wallet_address,
            "amount": float(loan.amount),
            "interest_rate": float(loan.interest_rate),
            "term_days": loan.term_days,
            "status": loan.status,
            "collateral_amount": float(loan.collateral_amount) if loan.collateral_amount else None,
            "collateral_token": loan.collateral_token,
            "created_at": loan.created_at.isoformat() if loan.created_at else None,
            "due_date": loan.due_date.isoformat() if loan.due_date else None,
            "repaid_at": loan.repaid_at.isoformat() if loan.repaid_at else None,
            "tx_hash": loan.tx_hash,
        }

