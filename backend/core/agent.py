"""
NeuroLend AI Agent for loan negotiation
Simple rule-based agent (can be upgraded to LangChain later)
"""
import os
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from services.scoring import ScoringService
from services.blockchain import BlockchainService
from services.loan_recommender import LoanRecommender
from services.preference_manager import PreferenceManager
from services.loan_marketplace import LoanMarketplace
from services.offer_aggregator import OfferAggregator
from core.nonce import nonce_manager
from core.signing import LoanOfferSigner

class NeuroLendAgent:
    """AI agent for loan negotiation"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.blockchain_service = BlockchainService()
        self.signer = LoanOfferSigner()
        self.lending_vault_address = os.getenv("LENDING_VAULT_ADDRESS")
        self.loan_recommender = LoanRecommender()
        self.preference_manager = PreferenceManager()
        self.marketplace = LoanMarketplace()
        self.offer_aggregator = OfferAggregator()
        
    async def process_chat(self, user_address: str, message: str) -> Dict:
        """
        Process a chat message and generate response
        
        Args:
            user_address: User's wallet address
            message: User's message
            
        Returns:
            Dict with 'response' (str) and optionally 'offer' (dict) and 'signature' (str)
        """
        message_lower = message.lower().strip()
        
        # Get user's score info first
        score_info = await self._get_score_info(user_address)
        score = score_info['score']
        risk_band = score_info['riskBand']
        
        # Check for greetings
        greeting_keywords = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        is_greeting = any(keyword in message_lower for keyword in greeting_keywords)
        
        # Check if user is requesting a loan
        loan_keywords = ['loan', 'borrow', 'lend', 'need', 'want', 'get', 'request', 'apply']
        is_loan_request = any(keyword in message_lower for keyword in loan_keywords)
        
        # Check for questions about score
        score_keywords = ['score', 'credit', 'rating', 'risk', 'tier', 'status']
        is_score_question = any(keyword in message_lower for keyword in score_keywords)
        
        # Extract amount if mentioned
        amount = self._extract_amount(message)
        
        # Handle different types of messages
        if is_greeting:
            risk_description = {1: "Low Risk", 2: "Medium Risk", 3: "High Risk"}.get(risk_band, "Unknown")
            return {
                "response": f"Hello! ðŸ‘‹ I'm your NeuroLend AI assistant. I can help you get a personalized loan based on your AETHER-SCORE score.\n\nYour current score is **{score}** ({risk_description}). This affects the loan terms I can offer you.\n\nHow can I help you today? You can:\n- Ask for a loan (e.g., 'I need 100 QIE')\n- Ask about your credit score\n- Get information about loan terms",
                "offer": None,
                "signature": None,
                "requiresSignature": False
            }
        elif is_score_question:
            risk_description = {1: "Low Risk", 2: "Medium Risk", 3: "High Risk"}.get(risk_band, "Unknown")
            risk_explanation = {
                1: "Excellent! You qualify for the best loan terms with low interest rates.",
                2: "Good! You can get competitive loan terms with moderate interest rates.",
                3: "Fair. You can still get loans, but with higher interest rates and more collateral required."
            }.get(risk_band, "Unknown risk level.")
            
            return {
                "response": f"ðŸ“Š **Your AETHER-SCORE Score: {score}**\n\n**Risk Band:** {risk_description}\n\n{risk_explanation}\n\nWould you like to apply for a loan? Just tell me how much you need!",
                "offer": None,
                "signature": None,
                "requiresSignature": False
            }
        elif is_loan_request and amount:
            # Generate loan offer
            return await self._generate_loan_offer(user_address, amount)
        elif is_loan_request:
            # Ask for amount
            return {
                "response": "I'd be happy to help you get a loan! ðŸ’°\n\nHow much QIE would you like to borrow? Just tell me the amount (e.g., 'I need 100 QIE' or 'I want to borrow 500 QIE').",
                "offer": None,
                "signature": None,
                "requiresSignature": False
            }
        else:
            # General conversation - be more helpful
            return {
                "response": f"I'm here to help you with loans! ðŸ’¬\n\nYour AETHER-SCORE score is **{score}** (Risk Band {risk_band}).\n\nYou can:\n- Request a loan: 'I need 100 QIE'\n- Ask about your score: 'What's my credit score?'\n- Get loan information: 'What are the loan terms?'\n\nWhat would you like to do?",
                "offer": None,
                "signature": None,
                "requiresSignature": False
            }
    
    async def _get_score_info(self, address: str) -> Dict:
        """Get user's AETHER-SCORE score"""
        try:
            # Try to get from blockchain first
            on_chain_score = await self.blockchain_service.get_score(address)
            if on_chain_score and on_chain_score["score"] > 0:
                return {
                    "score": on_chain_score["score"],
                    "riskBand": on_chain_score["riskBand"]
                }
            
            # Compute new score
            result = await self.scoring_service.compute_score(address)
            return {
                "score": result["score"],
                "riskBand": result["riskBand"]
            }
        except Exception as e:
            print(f"Error getting score: {e}")
            return {"score": 500, "riskBand": 2}
    
    async def _generate_loan_offer(self, borrower: str, requested_amount: float) -> Dict:
        """
        Generate a personalized loan offer based on AETHER-SCORE score
        
        Args:
            borrower: Borrower address
            requested_amount: Requested loan amount in QIE
            
        Returns:
            Dict with offer details and signature
        """
        # Get score
        score_info = await self._get_score_info(borrower)
        score = score_info["score"]
        risk_band = score_info["riskBand"]
        
        # Calculate loan terms based on score
        if score >= 750:
            # Low risk
            interest_rate = 450  # 4.5% APR in basis points
            ltv = 0.70  # 70% LTV
            rate_display = "4.5%"
        elif score >= 500:
            # Medium risk
            interest_rate = 750  # 7.5% APR
            ltv = 0.50  # 50% LTV
            rate_display = "7.5%"
        else:
            # High risk
            interest_rate = 1200  # 12% APR
            ltv = 0.30  # 30% LTV
            rate_display = "12%"
        
        # Calculate collateral needed
        collateral_amount = int(requested_amount / ltv * 1e18)  # Convert to wei
        loan_amount = int(requested_amount * 1e18)  # Convert to wei
        
        # Generate nonce
        nonce = nonce_manager.generate_nonce(borrower)
        
        # Set expiry (1 hour from now)
        expiry = int((datetime.now() + timedelta(hours=1)).timestamp())
        
        # Duration (30 days default)
        duration = 30 * 24 * 60 * 60  # 30 days in seconds
        
        # Create offer
        offer = {
            "borrower": borrower,
            "amount": loan_amount,
            "collateralAmount": collateral_amount,
            "interestRate": interest_rate,
            "duration": duration,
            "nonce": nonce,
            "expiry": expiry
        }
        
        # Sign offer
        if not self.lending_vault_address:
            signature = "0x" + "0" * 130  # Placeholder
        else:
            try:
                signature = self.signer.sign_loan_offer(offer, self.lending_vault_address)
            except Exception as e:
                # If signing fails, use placeholder (for demo purposes)
                from utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Failed to sign loan offer: {e}. Using placeholder signature.")
                signature = "0x" + "0" * 130
        
        # Generate response message
        response = (
            f"Great! Based on your AETHER-SCORE score of {score} (Risk Band {risk_band}), "
            f"I can offer you a loan with the following terms:\n\n"
            f"ðŸ’° Loan Amount: {requested_amount:.2f} QIE\n"
            f"ðŸ’Ž Collateral Required: {collateral_amount / 1e18:.2f} QIE\n"
            f"ðŸ“Š Interest Rate: {rate_display} APR\n"
            f"â±ï¸ Duration: 30 days\n\n"
            f"Would you like to accept this offer?"
        )
        
        return {
            "response": response,
            "offer": offer,
            "signature": signature,
            "requiresSignature": True
        }
    
    def _extract_amount(self, message: str) -> Optional[float]:
        """Extract loan amount from message"""
        import re
        
        # Look for numbers followed by QIE or just numbers
        patterns = [
            r'(\d+(?:\.\d+)?)\s*qie',
            r'(\d+(?:\.\d+)?)\s*usd',
            r'(\d+(?:\.\d+)?)\s*dollars',
            r'(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                try:
                    amount = float(match.group(1))
                    # Cap at reasonable amount for demo
                    return min(amount, 10000)
                except:
                    pass
        
        return None


