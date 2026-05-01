from fastapi import FastAPI, HTTPException, Request, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

from services.scoring import ScoringService
from services.blockchain import BlockchainService
from services.gdpr import GDPRService
from database.models import APIAccess
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.auth import get_current_user
from middleware.rate_limit import limiter
from utils.validators import validate_ethereum_address, validate_score, validate_risk_band, validate_message_length
from utils.sanitizers import sanitize_chat_message
from utils.wallet_verification import verify_timestamped_message, create_verification_message
from utils.audit_logger import log_score_generation, log_on_chain_update, log_loan_creation
from utils.jwt_handler import create_access_token
from models.auth import Token, AuthRequest
from utils.monitoring import init_sentry, capture_exception, set_user_context
from utils.logger import setup_logging, get_logger
from middleware.logging import LoggingMiddleware
from middleware.metrics import MetricsMiddleware
from middleware.performance import PerformanceMiddleware
from middleware.cache import CacheMiddleware
from utils.metrics import get_metrics, get_metrics_content_type, set_app_info

load_dotenv()

# Setup structured logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", os.path.join("logs", "app.log"))
)

logger = get_logger(__name__)

# Initialize Sentry before creating the app
init_sentry(
    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    enable_tracing=os.getenv("SENTRY_ENABLE_TRACING", "true").lower() == "true"
)

app = FastAPI(
    title="AETHER-SCORE API",
    version="1.0.0",
    description="""
    AETHER-SCORE API - AI-powered credit scoring on QIE blockchain.
    
    ## Features
    
    * **Credit Scoring**: Generate AI-powered credit scores based on on-chain activity
    * **Staking**: Stake NCRD tokens to boost your credit tier
    * **Lending**: Create and manage loans with AI negotiation
    * **Oracle Integration**: Real-time price and volatility data from QIE oracles
    * **Fraud Detection**: Advanced fraud detection and Sybil attack prevention
    
    ## Authentication
    
    Most endpoints require authentication via:
    * API Key in header: `X-API-Key: your-api-key`
    * JWT Token in header: `Authorization: Bearer your-jwt-token`
    * Wallet signature verification for blockchain operations
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Set application info for metrics
app_version = os.getenv("APP_VERSION", "1.0.0")
app_environment = os.getenv("ENVIRONMENT", "development")
set_app_info(app_version, app_environment)

# Add logging middleware (after CORS, before other middleware)
app.add_middleware(LoggingMiddleware)

# Add metrics middleware
if os.getenv("METRICS_ENABLED", "true").lower() == "true":
    app.add_middleware(MetricsMiddleware)

# Add performance monitoring middleware
if os.getenv("PERFORMANCE_MONITORING_ENABLED", "true").lower() == "true":
    app.add_middleware(PerformanceMiddleware)

# Add cache middleware (after logging, before other middleware)
if os.getenv("CACHE_ENABLED", "true").lower() == "true":
    app.add_middleware(CacheMiddleware)

# Add exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that sends errors to Sentry"""
    from utils.monitoring import capture_exception
    
    # Capture exception in Sentry
    capture_exception(
        exc,
        endpoint=request.url.path,
        method=request.method,
        query_params=str(request.query_params),
    )
    
    # Return error response
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )

# Security headers middleware (must be first)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware for frontend - allow all origins for hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Validate required environment variables at startup
def validate_environment():
    """Validate required environment variables and fail fast with clear errors"""
    required_vars = []
    missing_vars = []
    
    # Check contract address (accept both variants)
    contract_address = os.getenv("CREDIT_PASSPORT_NFT_ADDRESS") or os.getenv("CREDIT_PASSPORT_ADDRESS")
    if not contract_address:
        missing_vars.append("CREDIT_PASSPORT_NFT_ADDRESS (or CREDIT_PASSPORT_ADDRESS)")
    else:
        # Validate address format
        if not contract_address.startswith("0x") or len(contract_address) != 42:
            raise ValueError(
                f"Invalid CREDIT_PASSPORT_NFT_ADDRESS format: {contract_address}. "
                "Must be a valid Ethereum address (0x followed by 40 hex characters)."
            )
    
    # Check private key (try encrypted first, then plaintext)
    from utils.secrets_manager import get_secrets_manager
    secrets_manager = get_secrets_manager()
    private_key = secrets_manager.get_secret("BACKEND_PRIVATE_KEY_ENCRYPTED", encrypted=True)
    if not private_key:
        private_key = os.getenv("BACKEND_PRIVATE_KEY")
    if not private_key:
        missing_vars.append("BACKEND_PRIVATE_KEY (or BACKEND_PRIVATE_KEY_ENCRYPTED)")
    else:
        # Sanitize private key: strip whitespace
        private_key_sanitized = private_key.strip()
        private_key_sanitized = "".join(private_key_sanitized.split())
        
        # Handle missing 0x prefix
        if not private_key_sanitized.startswith("0x"):
            if len(private_key_sanitized) == 64:
                private_key_sanitized = "0x" + private_key_sanitized
            else:
                raise ValueError(
                    f"Invalid BACKEND_PRIVATE_KEY format. "
                    f"Expected 0x followed by 64 hex characters, got length {len(private_key_sanitized)}. "
                    f"Value: {private_key[:20]}... (truncated)"
                )
        
        # Validate private key format (basic check)
        if len(private_key_sanitized) != 66:
            raise ValueError(
                f"Invalid BACKEND_PRIVATE_KEY format. "
                f"Expected 66 characters (0x + 64 hex), got {len(private_key_sanitized)}. "
                f"Value: {private_key[:20]}... (truncated)"
            )
        
        # Validate hex characters
        try:
            int(private_key_sanitized[2:], 16)
        except ValueError as e:
            raise ValueError(
                f"Invalid BACKEND_PRIVATE_KEY format. "
                f"Contains non-hexadecimal characters. Error: {str(e)}"
            )
    
    # Check RPC URL (using network config)
    from config.network import get_network_config
    try:
        network_config = get_network_config()
        rpc_url = network_config.get_primary_rpc()
        if not rpc_url:
            missing_vars.append("QIE_RPC_URL (or network config)")
        else:
            # Validate RPC URL format
            if not rpc_url.startswith("http://") and not rpc_url.startswith("https://"):
                raise ValueError(
                    f"Invalid RPC URL format: {rpc_url}. "
                    "Must start with http:// or https://"
                )
    except Exception as e:
        logger.warning(f"Error getting network config: {e}")
        missing_vars.append("QIE_NETWORK or QIE_RPC_URL")
    
    if missing_vars:
        error_msg = (
            "Missing required environment variables:\n"
            + "\n".join(f"  - {var}" for var in missing_vars)
            + "\n\nPlease set these variables in your .env file or environment."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Environment validation passed")

# Run validation before initializing services
try:
    validate_environment()
    # Also run env schema validation
    from config.env import validate_env_on_startup
    validate_env_on_startup()
except ValueError as e:
    logger.error(f"Environment validation failed: {e}")
    raise

# Initialize database (if configured)
if os.getenv("DATABASE_URL"):
    from database.connection import init_db
    import asyncio
    # Initialize database on startup
    asyncio.create_task(init_db())

# Initialize services (these will also validate their own requirements)
try:
    scoring_service = ScoringService()
    blockchain_service = BlockchainService()
    gdpr_service = GDPRService()
    logger.info("All services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}", exc_info=True)
    raise

# Request/Response models
class ScoreRequest(BaseModel):
    address: str = Field(..., description="Ethereum wallet address")
    signature: Optional[str] = Field(None, description="EIP-191 signature proving wallet ownership")
    message: Optional[str] = Field(None, description="Message that was signed")
    timestamp: Optional[int] = Field(None, description="Timestamp from signed message")
    
    @validator('address')
    def validate_address(cls, v):
        return validate_ethereum_address(v)

class ScoreResponse(BaseModel):
    address: str
    score: int  # Final score
    baseScore: int = 0  # Base score before boosts
    riskBand: int
    explanation: str
    transactionHash: Optional[str] = None
    stakingBoost: int = 0
    oraclePenalty: int = 0
    stakedAmount: int = 0
    stakingTier: int = 0

class UpdateOnChainRequest(BaseModel):
    address: str = Field(..., description="Ethereum wallet address")
    score: int = Field(..., description="Credit score (0-1000)")
    riskBand: int = Field(..., description="Risk band (0-3)")
    
    @validator('address')
    def validate_address(cls, v):
        return validate_ethereum_address(v)
    
    @validator('score')
    def validate_score(cls, v):
        return validate_score(v)
    
    @validator('riskBand')
    def validate_risk_band(cls, v):
        return validate_risk_band(v)

class UpdateOnChainResponse(BaseModel):
    success: bool
    transactionHash: Optional[str] = None
    message: str

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """API root endpoint"""
    return {"message": "AETHER-SCORE API", "version": "1.0.0"}

@app.get("/health")
@limiter.exempt
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AETHER-SCORE API",
        "version": "1.0.0"
    }

@app.post("/api/auth/token", response_model=Token)
@limiter.limit("10/minute")
async def create_token(request: Request, auth_request: AuthRequest):
    """
    Create JWT token using wallet signature
    Alternative to API keys for user authentication
    """
    try:
        from utils.wallet_verification import verify_wallet_signature
        
        # Verify wallet signature
        if not verify_wallet_signature(
            auth_request.address,
            auth_request.message,
            auth_request.signature
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid wallet signature"
            )
        
        # Create JWT token
        access_token = create_access_token(
            data={"sub": auth_request.address, "role": "user"}
        )
        
        from utils.jwt_handler import JWT_EXPIRATION_HOURS
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/score", response_model=ScoreResponse)
@limiter.limit("10/minute")  # Stricter limit for score generation
async def generate_score(
    request: Request,
    score_request: ScoreRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Generate credit score for a wallet address and update on-chain
    Requires authentication (API key or JWT) or wallet signature
    """
    try:
        # Verify wallet signature if provided (alternative to API key/JWT)
        if score_request.signature and score_request.message and score_request.timestamp:
            verification_message = create_verification_message(
                score_request.address,
                "generate_score",
                score_request.timestamp
            )
            
            if not verify_timestamped_message(
                score_request.address,
                verification_message,
                score_request.signature,
                max_age_seconds=300
            ):
                log_score_generation(request, score_request.address, 0, "failure", "Invalid wallet signature")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid wallet signature"
                )
        elif not current_user:
            # In development, allow requests without authentication
            # In production, require authentication
            environment = os.getenv("ENVIRONMENT", "development")
            if environment.lower() not in ["development", "dev"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required (API key, JWT, or wallet signature)"
                )
        
        # Compute score (use async task if enabled, otherwise sync)
        use_async = os.getenv("USE_ASYNC_SCORE_COMPUTATION", "false").lower() == "true"
        
        if use_async:
            # Enqueue for background processing
            from rq import Queue
            from redis import Redis
            from tasks.score_tasks import compute_score_task
            
            redis_url = os.getenv("RQ_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/2")
            redis_conn = Redis.from_url(redis_url)
            queue = Queue("score_computation", connection=redis_conn)
            
            job = queue.enqueue(compute_score_task, score_request.address)
            
            # Return job ID, client can poll for result
            return ScoreResponse(
                address=score_request.address,
                score=0,  # Placeholder
                baseScore=0,
                riskBand=0,
                explanation="Score computation queued. Use job_id to check status.",
                transactionHash=None,
                stakingBoost=0,
                oraclePenalty=0,
                stakedAmount=0,
                stakingTier=0
            )
        else:
            # Compute synchronously
            result = await scoring_service.compute_score(score_request.address)
        
        # Automatically update on-chain
        tx_hash = None
        try:
            tx_hash = await blockchain_service.update_score(
                score_request.address,
                result["score"],
                result["riskBand"]
            )
            log_on_chain_update(request, score_request.address, tx_hash, "success")
        except Exception as e:
            # Log error but don't fail the request
            error_msg = str(e)
            log_on_chain_update(request, score_request.address, "", "failure", error_msg)
            # Continue without tx_hash
        
        # Log successful score generation
        log_score_generation(request, score_request.address, result["score"], "success")
        
        # Construct explorer URL if tx_hash exists (using network config)
        from config.network import get_network_config
        network_config = get_network_config()
        explorer_prefix = f"{network_config.explorer_url}/tx"
        tx_url = f"{explorer_prefix}/{tx_hash}" if tx_hash else None
        
        return ScoreResponse(
            address=score_request.address,
            score=result["score"],
            baseScore=result.get("baseScore", result["score"]),
            riskBand=result["riskBand"],
            explanation=result["explanation"],
            transactionHash=tx_hash,
            stakingBoost=result.get("stakingBoost", 0),
            oraclePenalty=result.get("oraclePenalty", 0),
            stakedAmount=result.get("stakedAmount", 0),
            stakingTier=result.get("stakingTier", 0)
        )
    except HTTPException:
        raise
    except Exception as e:
        log_score_generation(request, score_request.address, 0, "failure", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Score History API Models
class ScoreHistoryResponse(BaseModel):
    wallet_address: str
    history: List[Dict[str, Any]]
    total_count: int

class ScoreTrendsResponse(BaseModel):
    wallet_address: str
    current_score: int
    change_30d: int
    change_30d_percent: float
    trend_direction: str  # "up", "down", "stable"
    average_score: float
    highest_score: int
    lowest_score: int

class ScorePredictRequest(BaseModel):
    scenario: str = Field(..., description="Scenario type: loan_repayment, staking, transaction_volume, portfolio_diversification")
    scenario_data: Optional[Dict[str, Any]] = Field(None, description="Scenario-specific data")

class ScorePredictResponse(BaseModel):
    predicted_score: int
    predicted_change: int
    current_score: int
    confidence_level: float
    explanation: str
    scenario: str

@app.get("/api/score/{address}/history", response_model=ScoreHistoryResponse)
@limiter.limit("30/minute")
async def get_score_history(
    request: Request,
    address: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get score history for an address
    Query params: start_date (ISO format), end_date (ISO format), limit
    """
    try:
        from datetime import datetime
        from database.connection import get_db_session
        from database.repositories import ScoreHistoryRepository
        
        # Validate address
        address = validate_ethereum_address(address)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Fetch history
        async with get_db_session() as session:
            history_entries = await ScoreHistoryRepository.get_history(
                session, address, limit, start_dt, end_dt
            )
        
        # Convert to dict format
        history = []
        for entry in history_entries:
            history.append({
                "id": entry.id,
                "score": entry.score,
                "risk_band": entry.risk_band,
                "previous_score": entry.previous_score,
                "explanation": entry.explanation,
                "change_reason": entry.change_reason,
                "computed_at": entry.computed_at.isoformat() if entry.computed_at else None,
            })
        
        return ScoreHistoryResponse(
            wallet_address=address,
            history=history,
            total_count=len(history)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting score history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/score/{address}/trends", response_model=ScoreTrendsResponse)
@limiter.limit("30/minute")
async def get_score_trends(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get score trends and statistics for an address
    """
    try:
        from datetime import datetime, timedelta
        from database.connection import get_db_session
        from database.repositories import ScoreHistoryRepository, ScoreRepository
        
        # Validate address
        address = validate_ethereum_address(address)
        
        # Get current score
        async with get_db_session() as session:
            current_score_entry = await ScoreRepository.get_score(session, address)
            current_score = current_score_entry.score if current_score_entry else 0
            
            # Get history for last 30 days
            start_date = datetime.utcnow() - timedelta(days=30)
            history = await ScoreHistoryRepository.get_history(session, address, limit=100, start_date=start_date)
        
        if not history:
            return ScoreTrendsResponse(
                wallet_address=address,
                current_score=current_score,
                change_30d=0,
                change_30d_percent=0.0,
                trend_direction="stable",
                average_score=float(current_score),
                highest_score=current_score,
                lowest_score=current_score
            )
        
        # Calculate trends
        oldest_score = history[-1].score if history else current_score
        change_30d = current_score - oldest_score
        change_30d_percent = (change_30d / oldest_score * 100) if oldest_score > 0 else 0.0
        
        # Determine trend direction
        if change_30d > 10:
            trend_direction = "up"
        elif change_30d < -10:
            trend_direction = "down"
        else:
            trend_direction = "stable"
        
        # Calculate statistics
        scores = [entry.score for entry in history]
        scores.append(current_score)
        average_score = sum(scores) / len(scores) if scores else current_score
        highest_score = max(scores) if scores else current_score
        lowest_score = min(scores) if scores else current_score
        
        return ScoreTrendsResponse(
            wallet_address=address,
            current_score=current_score,
            change_30d=change_30d,
            change_30d_percent=change_30d_percent,
            trend_direction=trend_direction,
            average_score=average_score,
            highest_score=highest_score,
            lowest_score=lowest_score
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting score trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/score/{address}/predict", response_model=ScorePredictResponse)
@limiter.limit("20/minute")
async def predict_score_change(
    request: Request,
    address: str,
    predict_request: ScorePredictRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Predict score change based on scenario
    """
    try:
        from database.connection import get_db_session
        from database.repositories import ScoreRepository
        from services.score_predictor import ScorePredictorService
        
        # Validate address
        address = validate_ethereum_address(address)
        
        # Get current score
        async with get_db_session() as session:
            score_entry = await ScoreRepository.get_score(session, address)
            current_score = score_entry.score if score_entry else 500
        
        # Predict change
        prediction = ScorePredictorService.predict_score_change(
            current_score=current_score,
            scenario=predict_request.scenario,
            scenario_data=predict_request.scenario_data or {}
        )
        
        return ScorePredictResponse(**prediction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error predicting score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/score/{address}", response_model=ScoreResponse)
@limiter.limit("60/minute")
async def get_score(request: Request, address: str):
    """Get score for a wallet address (from blockchain or compute new)"""
    try:
        # Validate address
        address = validate_ethereum_address(address)
        # First try to get from blockchain
        on_chain_score = await blockchain_service.get_score(address)
        if on_chain_score and on_chain_score["score"] > 0:
            return ScoreResponse(
                address=address,
                score=on_chain_score["score"],
                baseScore=on_chain_score["score"],  # On-chain doesn't store breakdown
                riskBand=on_chain_score["riskBand"],
                explanation="Score retrieved from blockchain",
                transactionHash=None,
                stakingBoost=0,
                oraclePenalty=0,
                stakedAmount=0,
                stakingTier=0
            )
        
        # If not on-chain, compute new score
        result = await scoring_service.compute_score(address)
        return ScoreResponse(
            address=address,
            score=result["score"],
            baseScore=result.get("baseScore", result["score"]),
            riskBand=result["riskBand"],
            explanation=result["explanation"],
            transactionHash=None,
            stakingBoost=result.get("stakingBoost", 0),
            oraclePenalty=result.get("oraclePenalty", 0),
            stakedAmount=result.get("stakedAmount", 0),
            stakingTier=result.get("stakingTier", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/oracle/price")
@limiter.limit("60/minute")
async def get_oracle_price(request: Request):
    """Get current oracle price"""
    try:
        oracle_address = os.getenv("QIE_ORACLE_USD_ADDR")
        if not oracle_address or oracle_address == "0x0000000000000000000000000000000000000000":
            return {"price": None, "error": "Oracle address not configured"}
        
        from services.oracle import QIEOracleService
        oracle_service = QIEOracleService()
        price = await oracle_service.fetchOraclePrice(oracle_address)
        
        return {
            "price": price,
            "timestamp": int(__import__("time").time()),
            "oracleAddress": oracle_address
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/staking/{address}")
@limiter.limit("60/minute")
async def get_staking_info(request: Request, address: str):
    """Get staking information for an address"""
    try:
        # Validate address
        address = validate_ethereum_address(address)
        from services.staking import StakingService
        staking_service = StakingService()
        
        staked_amount = staking_service.get_staked_amount(address)
        tier = staking_service.get_integration_tier(address)
        boost = staking_service.calculate_staking_boost(tier)
        
        tier_names = {0: "None", 1: "Bronze", 2: "Silver", 3: "Gold"}
        
        return {
            "address": address,
            "stakedAmount": staked_amount,
            "tier": tier,
            "tierName": tier_names.get(tier, "Unknown"),
            "scoreBoost": boost
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lending/ltv/{address}")
@limiter.limit("60/minute")
async def get_ltv(request: Request, address: str):
    """Get LTV (Loan-to-Value) for an address"""
    try:
        # Validate address
        address = validate_ethereum_address(address)
        # Get score first
        result = await scoring_service.compute_score(address)
        risk_band = result["riskBand"]
        
        # Map risk band to LTV (basis points)
        ltv_map = {
            1: 7000,  # 70%
            2: 5000,  # 50%
            3: 3000,  # 30%
            0: 0      # No passport
        }
        
        ltv_bps = ltv_map.get(risk_band, 0)
        
        return {
            "address": address,
            "ltvBps": ltv_bps,
            "ltvPercent": ltv_bps / 100,
            "riskBand": risk_band,
            "score": result["score"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NeuroLend Chat API
class ChatRequest(BaseModel):
    address: str = Field(..., description="Ethereum wallet address")
    message: str = Field(..., description="Chat message")
    
    @validator('address')
    def validate_address(cls, v):
        return validate_ethereum_address(v)
    
    @validator('message')
    def validate_message(cls, v):
        return validate_message_length(v, max_length=1000)

class ChatResponse(BaseModel):
    response: str
    offer: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None
    requiresSignature: bool = False

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # Stricter limit for chat
async def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Chat with NeuroLend AI agent
    Requires authentication (API key or JWT) or wallet signature
    """
    try:
        # Sanitize message
        sanitized_message = sanitize_chat_message(chat_request.message)
        
        # Verify authentication or wallet signature
        # In development, allow requests without authentication
        # In production, require authentication
        if not current_user:
            environment = os.getenv("ENVIRONMENT", "development")
            if environment.lower() not in ["development", "dev"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
        
        from core.agent import NeuroLendAgent
        agent = NeuroLendAgent()
        result = await agent.process_chat(chat_request.address, sanitized_message)
        
        # Log chat interaction
        from utils.audit_logger import log_audit_event
        log_audit_event(
            request=request,
            action="chat_message",
            result="success",
            user_address=chat_request.address,
            metadata={"message_length": len(sanitized_message)}
        )
        
        return ChatResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Chat error: {str(e)}")
        print(f"Traceback: {error_trace}")
        from utils.audit_logger import log_audit_event
        log_audit_event(
            request=request,
            action="chat_message",
            result="failure",
            user_address=chat_request.address,
            error_message=str(e)
        )
        # In development, return more detailed error
        environment = os.getenv("ENVIRONMENT", "development")
        if environment.lower() in ["development", "dev"]:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Loan Management API Models
class LoanResponse(BaseModel):
    id: Optional[int] = None
    loan_id: int
    wallet_address: str
    amount: float
    interest_rate: float
    term_days: int
    status: str
    collateral_amount: Optional[float] = None
    collateral_token: Optional[str] = None
    created_at: Optional[str] = None
    due_date: Optional[str] = None
    repaid_at: Optional[str] = None
    tx_hash: Optional[str] = None

class LoansListResponse(BaseModel):
    loans: List[LoanResponse]
    total_count: int

class RepaymentScheduleResponse(BaseModel):
    loan_id: int
    schedule: List[Dict[str, Any]]
    total_principal: float
    total_interest: float
    total_amount: float

class EarlyRepaymentRequest(BaseModel):
    loan_id: int
    early_payment_date: str  # ISO format
    early_payment_amount: Optional[float] = None

class EarlyRepaymentResponse(BaseModel):
    savings: float
    interest_saved: float
    days_saved: int
    original_total: float
    early_total: float
    original_interest: float
    early_interest: float

class LoanComparisonRequest(BaseModel):
    loan1: Dict[str, Any]
    loan2: Dict[str, Any]

class LoanComparisonResponse(BaseModel):
    loan1: Dict[str, Any]
    loan2: Dict[str, Any]
    comparison: Dict[str, Any]

@app.get("/api/loans/{address}", response_model=LoansListResponse)
@limiter.limit("30/minute")
async def get_user_loans(
    request: Request,
    address: str,
    status: Optional[str] = None,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get all loans for a user
    Query param: status (optional filter: active, repaid, defaulted, liquidated)
    """
    try:
        from services.loan_service import LoanService
        
        # Validate address
        address = validate_ethereum_address(address)
        
        loan_service = LoanService()
        
        # Fetch loans (try database first, fallback to blockchain)
        loans = await loan_service.get_user_loans(address, from_db=True)
        
        # Filter by status if provided
        if status:
            loans = [loan for loan in loans if loan.get("status") == status]
        
        # Convert to response format
        loan_responses = [LoanResponse(**loan) for loan in loans]
        
        return LoansListResponse(
            loans=loan_responses,
            total_count=len(loan_responses)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting loans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/loans/{address}/active", response_model=LoansListResponse)
@limiter.limit("30/minute")
async def get_active_loans(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get only active loans for a user"""
    return await get_user_loans(request, address, status="active", current_user=current_user)

@app.get("/api/loans/{loan_id}/schedule", response_model=RepaymentScheduleResponse)
@limiter.limit("30/minute")
async def get_loan_schedule(
    request: Request,
    loan_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get repayment schedule for a specific loan
    """
    try:
        from services.loan_service import LoanService
        from database.connection import get_session
        from database.repositories import LoanRepository
        
        loan_service = LoanService()
        
        # Get loan from database
        async with get_session() as session:
            loans = await LoanRepository.get_user_loans(session, "")  # Get all loans
            loan = next((l for l in loans if l.loan_id == loan_id), None)
            
            if not loan:
                raise HTTPException(status_code=404, detail="Loan not found")
            
            # Calculate schedule
            schedule = loan_service.calculate_repayment_schedule(
                loan_amount=float(loan.amount),
                interest_rate=float(loan.interest_rate),
                term_days=loan.term_days,
                start_date=loan.created_at
            )
            
            # Calculate totals
            total_principal = float(loan.amount)
            total_interest = sum(payment["interest"] for payment in schedule)
            total_amount = total_principal + total_interest
            
            return RepaymentScheduleResponse(
                loan_id=loan_id,
                schedule=schedule,
                total_principal=total_principal,
                total_interest=total_interest,
                total_amount=total_amount
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting loan schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/loans/calculate-early-repayment", response_model=EarlyRepaymentResponse)
@limiter.limit("20/minute")
async def calculate_early_repayment(
    request: Request,
    repayment_request: EarlyRepaymentRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Calculate savings from early loan repayment
    """
    try:
        from datetime import datetime
        from services.loan_service import LoanService
        from database.connection import get_session
        from database.repositories import LoanRepository
        
        loan_service = LoanService()
        
        # Get loan from database
        async with get_session() as session:
            loans = await LoanRepository.get_user_loans(session, "")
            loan = next((l for l in loans if l.loan_id == repayment_request.loan_id), None)
            
            if not loan:
                raise HTTPException(status_code=404, detail="Loan not found")
            
            # Parse early payment date
            early_date = datetime.fromisoformat(repayment_request.early_payment_date.replace('Z', '+00:00'))
            
            # Calculate savings
            savings = loan_service.calculate_early_repayment_savings(
                loan_amount=float(loan.amount),
                interest_rate=float(loan.interest_rate),
                term_days=loan.term_days,
                early_payment_date=early_date,
                start_date=loan.created_at
            )
            
            return EarlyRepaymentResponse(**savings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating early repayment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/loans/compare", response_model=LoanComparisonResponse)
@limiter.limit("20/minute")
async def compare_loans(
    request: Request,
    comparison_request: LoanComparisonRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Compare two loan offers
    """
    try:
        from services.loan_service import LoanService
        
        loan_service = LoanService()
        comparison = loan_service.compare_loans(
            comparison_request.loan1,
            comparison_request.loan2
        )
        
        return LoanComparisonResponse(**comparison)
    except Exception as e:
        logger.error(f"Error comparing loans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Portfolio API Models
class TokenHoldingsResponse(BaseModel):
    wallet_address: str
    holdings: List[Dict[str, Any]]
    total_value_usd: float

class TransactionHistoryResponse(BaseModel):
    wallet_address: str
    transactions: List[Dict[str, Any]]
    total_count: int
    page: int = 1
    limit: int = 100

class DeFiActivityResponse(BaseModel):
    wallet_address: str
    protocols: List[Dict[str, Any]]
    total_protocols: int
    total_interactions: int
    total_volume: float

class RiskAssessmentResponse(BaseModel):
    wallet_address: str
    risk_score: int
    risk_level: str
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    assessment_date: str

@app.get("/api/portfolio/{address}/holdings", response_model=TokenHoldingsResponse)
@limiter.limit("30/minute")
async def get_token_holdings(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get token holdings breakdown for an address
    """
    try:
        from services.portfolio_service import PortfolioService
        
        # Validate address
        address = validate_ethereum_address(address)
        
        portfolio_service = PortfolioService()
        holdings = await portfolio_service.get_token_holdings(address)
        
        total_value = sum(h["usd_value"] for h in holdings)
        
        return TokenHoldingsResponse(
            wallet_address=address,
            holdings=holdings,
            total_value_usd=total_value
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting token holdings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/portfolio/{address}/transactions", response_model=TransactionHistoryResponse)
@limiter.limit("30/minute")
async def get_transaction_history(
    request: Request,
    address: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tx_type: Optional[str] = None,
    limit: int = 100,
    page: int = 1,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get transaction history for an address
    Query params: start_date, end_date, tx_type, limit, page
    """
    try:
        from datetime import datetime
        from database.connection import get_session
        from database.repositories import TransactionRepository
        
        # Validate address
        address = validate_ethereum_address(address)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Fetch transactions
        async with get_session() as session:
            transactions_list = await TransactionRepository.get_transactions_by_user(
                session, address, tx_type, limit * page
            )
        
        # Apply date filters if provided
        if start_dt or end_dt:
            filtered = []
            for tx in transactions_list:
                tx_date = tx.block_timestamp
                if tx_date:
                    if start_dt and tx_date < start_dt:
                        continue
                    if end_dt and tx_date > end_dt:
                        continue
                filtered.append(tx)
            transactions_list = filtered
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated = transactions_list[start_idx:end_idx]
        
        # Convert to dict format
        transactions = []
        for tx in paginated:
            transactions.append({
                "id": tx.id,
                "tx_hash": tx.tx_hash,
                "tx_type": tx.tx_type,
                "block_number": tx.block_number,
                "block_timestamp": tx.block_timestamp.isoformat() if tx.block_timestamp else None,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "value": float(tx.value) / 1e18 if tx.value else None,
                "gas_used": tx.gas_used,
                "status": tx.status,
                "contract_address": tx.contract_address,
            })
        
        return TransactionHistoryResponse(
            wallet_address=address,
            transactions=transactions,
            total_count=len(transactions_list),
            page=page,
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/portfolio/{address}/defi-activity", response_model=DeFiActivityResponse)
@limiter.limit("30/minute")
async def get_defi_activity(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get DeFi activity summary for an address
    """
    try:
        from services.portfolio_service import PortfolioService
        
        # Validate address
        address = validate_ethereum_address(address)
        
        portfolio_service = PortfolioService()
        activity = await portfolio_service.get_defi_activity(address)
        
        return DeFiActivityResponse(
            wallet_address=address,
            **activity
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting DeFi activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/portfolio/{address}/risk-assessment", response_model=RiskAssessmentResponse)
@limiter.limit("20/minute")
async def get_risk_assessment(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get portfolio risk assessment for an address
    """
    try:
        from services.portfolio_service import PortfolioService
        
        # Validate address
        address = validate_ethereum_address(address)
        
        portfolio_service = PortfolioService()
        assessment = await portfolio_service.assess_portfolio_risk(address)
        
        return RiskAssessmentResponse(
            wallet_address=address,
            **assessment
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting risk assessment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/update-on-chain", response_model=UpdateOnChainResponse)
@limiter.limit("10/minute")
async def update_on_chain(
    request: Request,
    update_request: UpdateOnChainRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Update score on blockchain
    Requires authentication (API key or JWT) or wallet signature
    """
    try:
        # Require authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        tx_hash = await blockchain_service.update_score(
            update_request.address,
            update_request.score,
            update_request.riskBand
        )
        
        log_on_chain_update(request, update_request.address, tx_hash, "success")
        
        return UpdateOnChainResponse(
            success=True,
            transactionHash=tx_hash,
            message="Score updated on-chain successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_on_chain_update(request, update_request.address, "", "failure", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# DeFi Integration API Models
class LoanOfferCreate(BaseModel):
    lender_address: str
    amount_min: float
    amount_max: float
    interest_rate: float
    term_days_min: int
    term_days_max: int
    collateral_required: bool = False
    accepted_collateral_tokens: Optional[List[str]] = None
    ltv_ratio: Optional[float] = None
    expires_at: Optional[str] = None
    borrower_address: Optional[str] = None

class LoanRequestCreate(BaseModel):
    borrower_address: str
    amount: float
    max_interest_rate: float
    term_days: int
    collateral_amount: Optional[float] = None
    collateral_tokens: Optional[List[str]] = None
    request_type: str = "standard"
    auction_end_time: Optional[str] = None

class OfferComparisonRequest(BaseModel):
    offer_ids: List[int]
    amount: float
    term_days: int

class CollateralAdd(BaseModel):
    token_address: str
    amount: float

class CollateralRemove(BaseModel):
    token_address: str
    amount: float

class RebalanceRequest(BaseModel):
    strategy: str = "diversification"

# Marketplace API Endpoints
@app.get("/api/marketplace/offers")
@limiter.limit("60/minute")
async def browse_offers(
    request: Request,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    max_interest_rate: Optional[float] = None,
    term_days: Optional[int] = None,
    borrower_address: Optional[str] = None,
    limit: int = 100
):
    """Browse available loan offers"""
    try:
        from services.loan_marketplace import LoanMarketplace
        from database.connection import get_session
        from decimal import Decimal
        
        marketplace = LoanMarketplace()
        filters = {}
        if amount_min:
            filters['amount_min'] = Decimal(str(amount_min))
        if amount_max:
            filters['amount_max'] = Decimal(str(amount_max))
        if max_interest_rate:
            filters['max_interest_rate'] = Decimal(str(max_interest_rate))
        if term_days:
            filters['term_days'] = term_days
        if borrower_address:
            filters['borrower_address'] = validate_ethereum_address(borrower_address)
        
        async with get_session() as session:
            offers = await marketplace.get_available_offers(filters, limit, session)
        
        return {"offers": offers}
    except Exception as e:
        logger.error(f"Error browsing offers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/marketplace/offers")
@limiter.limit("20/minute")
async def create_offer(
    request: Request,
    offer_data: LoanOfferCreate,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Create a loan offer"""
    try:
        from services.loan_marketplace import LoanMarketplace
        from database.connection import get_session
        from decimal import Decimal
        from datetime import datetime
        
        marketplace = LoanMarketplace()
        expires_at = None
        if offer_data.expires_at:
            expires_at = datetime.fromisoformat(offer_data.expires_at.replace('Z', '+00:00'))
        
        async with get_session() as session:
            offer = await marketplace.create_offer(
                validate_ethereum_address(offer_data.lender_address),
                Decimal(str(offer_data.amount_min)),
                Decimal(str(offer_data.amount_max)),
                Decimal(str(offer_data.interest_rate)),
                offer_data.term_days_min,
                offer_data.term_days_max,
                offer_data.collateral_required,
                offer_data.accepted_collateral_tokens,
                Decimal(str(offer_data.ltv_ratio)) if offer_data.ltv_ratio else None,
                expires_at,
                validate_ethereum_address(offer_data.borrower_address) if offer_data.borrower_address else None,
                None,
                session
            )
        
        if not offer:
            raise HTTPException(status_code=400, detail="Failed to create offer")
        
        return offer
    except Exception as e:
        logger.error(f"Error creating offer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/marketplace/offers/{offer_id}/accept")
@limiter.limit("20/minute")
async def accept_offer(
    request: Request,
    offer_id: int,
    borrower_address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Accept a loan offer"""
    try:
        from services.loan_marketplace import LoanMarketplace
        from database.connection import get_session
        
        marketplace = LoanMarketplace()
        borrower_address = validate_ethereum_address(borrower_address)
        
        async with get_session() as session:
            success = await marketplace.accept_offer(offer_id, borrower_address, session)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to accept offer")
        
        return {"success": True, "message": "Offer accepted"}
    except Exception as e:
        logger.error(f"Error accepting offer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/marketplace/compare")
@limiter.limit("30/minute")
async def compare_offers(
    request: Request,
    comparison: OfferComparisonRequest
):
    """Compare multiple offers side-by-side"""
    try:
        from services.rate_comparator import RateComparator
        from services.loan_marketplace import LoanMarketplace
        from database.connection import get_session
        from decimal import Decimal
        
        comparator = RateComparator()
        marketplace = LoanMarketplace()
        
        # Get offers
        offers = []
        async with get_session() as session:
            for offer_id in comparison.offer_ids:
                # Simplified: would need get_offer_by_id method
                all_offers = await marketplace.get_available_offers({}, 1000, session)
                offer = next((o for o in all_offers if o['id'] == offer_id), None)
                if offer:
                    offers.append(offer)
        
        matrix = await comparator.generate_comparison_matrix(
            offers,
            Decimal(str(comparison.amount)),
            comparison.term_days
        )
        
        return matrix
    except Exception as e:
        logger.error(f"Error comparing offers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Collateral API Endpoints
@app.get("/api/collateral/{loan_id}")
@limiter.limit("60/minute")
async def get_collateral_positions(
    request: Request,
    loan_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get collateral positions for a loan"""
    try:
        from services.collateral_manager import CollateralManager
        from database.connection import get_session
        
        manager = CollateralManager()
        
        async with get_session() as session:
            positions = await manager.get_collateral_positions(loan_id, session)
        
        return {"loan_id": loan_id, "positions": positions}
    except Exception as e:
        logger.error(f"Error getting collateral positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/collateral/{loan_id}/add")
@limiter.limit("20/minute")
async def add_collateral(
    request: Request,
    loan_id: int,
    collateral: CollateralAdd,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Add collateral to a loan"""
    try:
        from services.collateral_manager import CollateralManager
        from database.connection import get_session
        from decimal import Decimal
        
        manager = CollateralManager()
        
        async with get_session() as session:
            position = await manager.add_collateral(
                loan_id,
                validate_ethereum_address(collateral.token_address),
                Decimal(str(collateral.amount)),
                session
            )
        
        if not position:
            raise HTTPException(status_code=400, detail="Failed to add collateral")
        
        return position
    except Exception as e:
        logger.error(f"Error adding collateral: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/collateral/{loan_id}/health")
@limiter.limit("60/minute")
async def get_collateral_health(
    request: Request,
    loan_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get collateral health for a loan"""
    try:
        from services.collateral_health import CollateralHealthMonitor
        from database.connection import get_session
        
        monitor = CollateralHealthMonitor()
        
        async with get_session() as session:
            health = await monitor.monitor_health(loan_id, session)
        
        return health
    except Exception as e:
        logger.error(f"Error getting collateral health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/collateral/{loan_id}/rebalance-suggestions")
@limiter.limit("30/minute")
async def get_rebalance_suggestions(
    request: Request,
    loan_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get rebalancing suggestions for a loan"""
    try:
        from services.collateral_rebalancer import CollateralRebalancer
        from database.connection import get_session
        
        rebalancer = CollateralRebalancer()
        
        async with get_session() as session:
            suggestions = await rebalancer.get_rebalance_suggestions(loan_id, session)
        
        return {"loan_id": loan_id, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting rebalance suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Yield API Endpoints
@app.get("/api/yield/strategies")
@limiter.limit("60/minute")
async def get_yield_strategies(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get user yield strategies"""
    try:
        from services.yield_optimizer import YieldOptimizer
        from database.connection import get_session
        
        optimizer = YieldOptimizer()
        address = validate_ethereum_address(address)
        
        async with get_session() as session:
            portfolio = await optimizer.analyze_portfolio(address, session)
        
        return portfolio
    except Exception as e:
        logger.error(f"Error getting yield strategies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/yield/suggestions")
@limiter.limit("30/minute")
async def get_yield_suggestions(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get yield optimization suggestions"""
    try:
        from services.yield_optimizer import YieldOptimizer
        from database.connection import get_session
        
        optimizer = YieldOptimizer()
        address = validate_ethereum_address(address)
        
        async with get_session() as session:
            suggestions = await optimizer.suggest_strategies(address, session)
        
        return {"address": address, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting yield suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/yield/staking-advisor")
@limiter.limit("30/minute")
async def get_staking_advisor(
    request: Request,
    address: str,
    target_score_boost: Optional[int] = None,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get staking recommendations"""
    try:
        from services.staking_advisor import StakingAdvisor
        from database.connection import get_session
        
        advisor = StakingAdvisor()
        address = validate_ethereum_address(address)
        
        async with get_session() as session:
            recommendation = await advisor.suggest_staking_amount(target_score_boost or 100, None)
        
        return {"address": address, **recommendation}
    except Exception as e:
        logger.error(f"Error getting staking advisor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/yield/auto-compound/{strategy_id}/enable")
@limiter.limit("20/minute")
async def enable_auto_compound(
    request: Request,
    strategy_id: int,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Enable auto-compounding for a strategy"""
    try:
        from services.auto_compound import AutoCompoundService
        from database.connection import get_session
        
        service = AutoCompoundService()
        address = validate_ethereum_address(address)
        
        async with get_session() as session:
            success = await service.enable_auto_compound(address, strategy_id, session)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to enable auto-compound")
        
        return {"success": True, "message": "Auto-compound enabled"}
    except Exception as e:
        logger.error(f"Error enabling auto-compound: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/yield/protocols")
@limiter.limit("60/minute")
async def get_yield_protocols(request: Request):
    """Get available yield protocols"""
    try:
        from services.yield_farming import YieldFarmingService
        
        service = YieldFarmingService()
        protocols = await service.get_protocols()
        
        return {"protocols": protocols}
    except Exception as e:
        logger.error(f"Error getting yield protocols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# AI & Automation API Endpoints

# Loan Recommendation Endpoints
@app.get("/api/ai/recommendations")
@limiter.limit("30/minute")
async def get_loan_recommendations(
    request: Request,
    address: str,
    constraints: Optional[str] = None,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get AI loan recommendations"""
    try:
        from services.loan_recommender import LoanRecommender
        import json
        
        recommender = LoanRecommender()
        address = validate_ethereum_address(address)
        
        constraints_dict = json.loads(constraints) if constraints else {}
        
        recommendation = await recommender.recommend_loan_amount(address, constraints_dict)
        terms = await recommender.recommend_loan_terms(address, Decimal(str(recommendation.get('recommended_amount', 0))))
        
        return {
            "address": address,
            "amount_recommendation": recommendation,
            "terms_recommendation": terms,
        }
    except Exception as e:
        logger.error(f"Error getting loan recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/ai/recommendations/calculate-affordability")
@limiter.limit("30/minute")
async def calculate_affordability(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Calculate borrowing capacity"""
    try:
        from services.loan_recommender import LoanRecommender
        
        recommender = LoanRecommender()
        address = validate_ethereum_address(address)
        
        affordability = await recommender.calculate_affordability(address)
        
        return affordability
    except Exception as e:
        logger.error(f"Error calculating affordability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ai/preferences")
@limiter.limit("60/minute")
async def get_user_preferences(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get user preferences"""
    try:
        from services.preference_manager import PreferenceManager
        
        manager = PreferenceManager()
        address = validate_ethereum_address(address)
        
        preferences = await manager.get_preferences(address)
        
        if not preferences:
            return {"message": "No preferences found", "preferences": None}
        
        return preferences
    except Exception as e:
        logger.error(f"Error getting preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/ai/preferences")
@limiter.limit("20/minute")
async def save_user_preferences(
    request: Request,
    preferences: Dict[str, Any],
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Save user preferences"""
    try:
        from services.preference_manager import PreferenceManager
        
        manager = PreferenceManager()
        address = validate_ethereum_address(address)
        
        saved = await manager.save_preferences(address, preferences)
        
        if not saved:
            raise HTTPException(status_code=400, detail="Failed to save preferences")
        
        return saved
    except Exception as e:
        logger.error(f"Error saving preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Auto-Negotiation Endpoints
@app.post("/api/ai/negotiate/start")
@limiter.limit("20/minute")
async def start_negotiation(
    request: Request,
    loan_request: Dict[str, Any],
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Start auto-negotiation"""
    try:
        from services.auto_negotiation import AutoNegotiationService
        
        service = AutoNegotiationService()
        address = validate_ethereum_address(address)
        
        result = await service.start_negotiation(address, loan_request)
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to start negotiation")
        
        return result
    except Exception as e:
        logger.error(f"Error starting negotiation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ai/negotiate/{negotiation_id}")
@limiter.limit("60/minute")
async def get_negotiation_status(
    request: Request,
    negotiation_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get negotiation status"""
    try:
        from services.auto_negotiation import AutoNegotiationService
        
        service = AutoNegotiationService()
        
        status = await service.get_negotiation_status(negotiation_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        
        return status
    except Exception as e:
        logger.error(f"Error getting negotiation status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/ai/negotiate/{negotiation_id}/cancel")
@limiter.limit("20/minute")
async def cancel_negotiation(
    request: Request,
    negotiation_id: int,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Cancel negotiation"""
    try:
        from services.auto_negotiation import AutoNegotiationService
        
        service = AutoNegotiationService()
        address = validate_ethereum_address(address)
        
        success = await service.cancel_negotiation(negotiation_id, address)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel negotiation")
        
        return {"success": True, "message": "Negotiation cancelled"}
    except Exception as e:
        logger.error(f"Error cancelling negotiation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Risk Alert Endpoints
@app.get("/api/alerts")
@limiter.limit("60/minute")
async def get_alerts(
    request: Request,
    address: str,
    include_read: bool = False,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get user alerts"""
    try:
        from services.alert_engine import AlertEngine
        
        engine = AlertEngine()
        address = validate_ethereum_address(address)
        
        alerts = await engine.get_active_alerts(address, include_read)
        
        return {"address": address, "alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/alerts/{alert_id}/read")
@limiter.limit("30/minute")
async def mark_alert_read(
    request: Request,
    alert_id: int,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Mark alert as read"""
    try:
        from services.alert_engine import AlertEngine
        
        engine = AlertEngine()
        address = validate_ethereum_address(address)
        
        success = await engine.mark_alert_read(alert_id, address)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error marking alert as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/alerts/{alert_id}/dismiss")
@limiter.limit("30/minute")
async def dismiss_alert(
    request: Request,
    alert_id: int,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Dismiss alert"""
    try:
        from services.alert_engine import AlertEngine
        
        engine = AlertEngine()
        address = validate_ethereum_address(address)
        
        success = await engine.dismiss_alert(alert_id, address)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error dismissing alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/alerts/preferences")
@limiter.limit("60/minute")
async def get_notification_preferences(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get notification preferences"""
    try:
        from services.notification_service import NotificationService
        
        service = NotificationService()
        address = validate_ethereum_address(address)
        
        prefs = await service._get_notification_preferences(address)
        
        return prefs or {}
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/alerts/preferences")
@limiter.limit("20/minute")
async def update_notification_preferences(
    request: Request,
    preferences: Dict[str, Any],
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Update notification preferences"""
    try:
        from database.connection import get_session
        from database.models import NotificationPreference
        from sqlalchemy import select
        
        address = validate_ethereum_address(address)
        
        async with get_session() as session:
            result = await session.execute(
                select(NotificationPreference).where(NotificationPreference.wallet_address == address)
            )
            prefs = result.scalar_one_or_none()
            
            if prefs:
                prefs.in_app_enabled = preferences.get('in_app_enabled', True)
                prefs.email_enabled = preferences.get('email_enabled', False)
                prefs.push_enabled = preferences.get('push_enabled', False)
                if 'email_address' in preferences:
                    prefs.email_address = preferences['email_address']
            else:
                prefs = NotificationPreference(
                    wallet_address=address,
                    in_app_enabled=preferences.get('in_app_enabled', True),
                    email_enabled=preferences.get('email_enabled', False),
                    push_enabled=preferences.get('push_enabled', False),
                    email_address=preferences.get('email_address')
                )
                session.add(prefs)
            
            await session.commit()
        
        return {"success": True, "preferences": preferences}
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Predictive Analytics Endpoints
@app.post("/api/ai/predict/default-probability")
@limiter.limit("30/minute")
async def predict_default_probability(
    request: Request,
    address: str,
    loan_amount: float,
    term_days: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Predict default probability"""
    try:
        from services.default_predictor import DefaultPredictor
        from decimal import Decimal
        
        predictor = DefaultPredictor()
        address = validate_ethereum_address(address)
        
        prediction = await predictor.predict_default_probability(
            address,
            Decimal(str(loan_amount)),
            term_days
        )
        
        return prediction
    except Exception as e:
        logger.error(f"Error predicting default probability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ai/timing-advisor")
@limiter.limit("30/minute")
async def get_timing_advisor(
    request: Request,
    address: str,
    desired_amount: Optional[float] = None,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get optimal borrowing timing"""
    try:
        from services.timing_advisor import TimingAdvisor
        from decimal import Decimal
        
        advisor = TimingAdvisor()
        address = validate_ethereum_address(address)
        
        timing = await advisor.suggest_borrowing_timing(
            address,
            Decimal(str(desired_amount)) if desired_amount else Decimal('0')
        )
        
        return timing
    except Exception as e:
        logger.error(f"Error getting timing advisor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/ai/market-impact")
@limiter.limit("30/minute")
async def get_market_impact(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get market impact analysis"""
    try:
        from services.market_impact_analyzer import MarketImpactAnalyzer
        
        analyzer = MarketImpactAnalyzer()
        address = validate_ethereum_address(address)
        
        impact = await analyzer.analyze_market_impact_on_credit(address)
        
        return impact
    except Exception as e:
        logger.error(f"Error getting market impact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Social & Community API Endpoints

# Social Sharing Endpoints
@app.get("/api/social/badge/{address}")
@limiter.limit("60/minute")
async def get_badge(
    request: Request,
    address: str,
    style: str = "minimal",
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get badge image/data"""
    try:
        from services.badge_generator import BadgeGenerator
        
        generator = BadgeGenerator()
        address = validate_ethereum_address(address)
        
        badge = await generator.generate_score_badge(address, style)
        
        return badge
    except Exception as e:
        logger.error(f"Error getting badge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/social/share")
@limiter.limit("30/minute")
async def record_share(
    request: Request,
    share_data: Dict[str, Any],
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Record share event"""
    try:
        from database.connection import get_session
        from database.models import ScoreShare
        
        address = validate_ethereum_address(address)
        share_type = share_data.get('share_type', 'custom')
        badge_style = share_data.get('badge_style', 'minimal')
        share_url = share_data.get('share_url')
        
        async with get_session() as session:
            share = ScoreShare(
                wallet_address=address,
                share_type=share_type,
                badge_style=badge_style,
                share_url=share_url
            )
            session.add(share)
            await session.commit()
        
        return {"success": True, "share_id": share.id}
    except Exception as e:
        logger.error(f"Error recording share: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/social/verify/{address}")
@limiter.limit("60/minute")
async def get_verification_proof(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get on-chain verification proof"""
    try:
        from services.onchain_proof import OnChainProofService
        
        service = OnChainProofService()
        address = validate_ethereum_address(address)
        
        proof = await service.generate_proof_data(address)
        
        return proof
    except Exception as e:
        logger.error(f"Error getting verification proof: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/social/share-links/{address}")
@limiter.limit("60/minute")
async def get_share_links(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get share links for all platforms"""
    try:
        from services.social_share import SocialShareService
        
        service = SocialShareService()
        address = validate_ethereum_address(address)
        
        share_links = await service.generate_share_links(address)
        
        return share_links
    except Exception as e:
        logger.error(f"Error getting share links: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Leaderboard Endpoints
@app.get("/api/leaderboard/top")
@limiter.limit("60/minute")
async def get_top_scores(
    request: Request,
    limit: int = 100,
    timeframe: Optional[str] = None,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get top scores"""
    try:
        from services.leaderboard import LeaderboardService
        
        service = LeaderboardService()
        
        top_scores = await service.get_top_scores(limit, timeframe)
        
        return {"leaderboard": top_scores, "limit": limit, "timeframe": timeframe or "all_time"}
    except Exception as e:
        logger.error(f"Error getting top scores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/leaderboard/rank/{address}")
@limiter.limit("60/minute")
async def get_user_rank(
    request: Request,
    address: str,
    category: str = "all_time",
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get user rank"""
    try:
        from services.leaderboard import LeaderboardService
        
        service = LeaderboardService()
        address = validate_ethereum_address(address)
        
        rank = await service.get_user_rank(address, category)
        
        if not rank:
            raise HTTPException(status_code=404, detail="User not found in leaderboard")
        
        return rank
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user rank: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/leaderboard/{category}")
@limiter.limit("60/minute")
async def get_leaderboard_category(
    request: Request,
    category: str,
    limit: int = 100,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get leaderboard by category"""
    try:
        from services.leaderboard import LeaderboardService
        
        service = LeaderboardService()
        
        leaderboard = await service.get_leaderboard_category(category, limit)
        
        return {"category": category, "leaderboard": leaderboard}
    except Exception as e:
        logger.error(f"Error getting leaderboard category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Referral Rewards Endpoints
@app.get("/api/referrals/rewards/pending")
@limiter.limit("60/minute")
async def get_pending_rewards(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get pending rewards"""
    try:
        from services.referral_rewards import ReferralRewardsService
        
        service = ReferralRewardsService()
        address = validate_ethereum_address(address)
        
        rewards = await service.get_pending_rewards(address)
        
        return {"address": address, "pending_rewards": rewards}
    except Exception as e:
        logger.error(f"Error getting pending rewards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/referrals/rewards/distribute")
@limiter.limit("10/minute")
async def trigger_distribution(
    request: Request,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Trigger distribution (admin only)"""
    try:
        from services.token_distributor import TokenDistributorService
        
        service = TokenDistributorService()
        
        # Check threshold
        threshold_check = await service.check_distribution_threshold()
        
        if not threshold_check.get("threshold_reached", False):
            return {
                "success": False,
                "message": "Threshold not reached",
                "threshold_check": threshold_check,
            }
        
        # Execute distribution
        result = await service.execute_onchain_distribution()
        
        return result
    except Exception as e:
        logger.error(f"Error triggering distribution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/referrals/rewards/history")
@limiter.limit("60/minute")
async def get_reward_history(
    request: Request,
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get reward history"""
    try:
        from database.connection import get_session
        from database.models import ReferralReward
        from sqlalchemy import select
        
        address = validate_ethereum_address(address)
        
        async with get_session() as session:
            result = await session.execute(
                select(ReferralReward).where(
                    ReferralReward.recipient_address == address
                ).order_by(ReferralReward.created_at.desc()).limit(100)
            )
            rewards = result.scalars().all()
            
            return {
                "address": address,
                "rewards": [
                    {
                        "id": r.id,
                        "reward_type": r.reward_type,
                        "amount_ncrd": float(r.amount_ncrd),
                        "status": r.status,
                        "distribution_tx_hash": r.distribution_tx_hash,
                        "distributed_at": r.distributed_at.isoformat() if r.distributed_at else None,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in rewards
                ],
            }
    except Exception as e:
        logger.error(f"Error getting reward history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Team Score Endpoints
@app.post("/api/teams/create")
@limiter.limit("20/minute")
async def create_team(
    request: Request,
    team_data: Dict[str, Any],
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Create team"""
    try:
        from services.team_score import TeamScoreService
        
        service = TeamScoreService()
        address = validate_ethereum_address(address)
        
        team = await service.create_team(
            team_data.get('team_name'),
            address,
            team_data.get('member_addresses', []),
            team_data.get('team_type', 'custom')
        )
        
        if not team:
            raise HTTPException(status_code=400, detail="Failed to create team")
        
        return team
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/teams/{team_id}/members")
@limiter.limit("30/minute")
async def add_team_member(
    request: Request,
    team_id: int,
    member_data: Dict[str, Any],
    address: str,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Add team member"""
    try:
        from services.team_score import TeamScoreService
        
        service = TeamScoreService()
        address = validate_ethereum_address(address)
        member_address = validate_ethereum_address(member_data.get('member_address'))
        
        success = await service.add_team_member(team_id, member_address, address)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add team member")
        
        return {"success": True, "message": "Team member added"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding team member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/teams/{team_id}/score")
@limiter.limit("60/minute")
async def get_team_score(
    request: Request,
    team_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get team score"""
    try:
        from services.team_score import TeamScoreService
        
        service = TeamScoreService()
        
        score = await service.calculate_team_score(team_id)
        
        if not score:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return score
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/teams/leaderboard")
@limiter.limit("60/minute")
async def get_team_leaderboard(
    request: Request,
    limit: int = 100,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get team leaderboard"""
    try:
        from services.team_score import TeamScoreService
        
        service = TeamScoreService()
        
        leaderboard = await service.get_team_leaderboard(limit)
        
        return {"leaderboard": leaderboard, "limit": limit}
    except Exception as e:
        logger.error(f"Error getting team leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ========== Analytics & Reporting Endpoints ==========

async def get_wallet_address(request: Request) -> Optional[str]:
    """Extract wallet address from request (header, query param, or authenticated user)"""
    # Try header first
    address = request.headers.get("X-Wallet-Address")
    if address:
        return address
    
    # Try query param
    address = request.query_params.get("address")
    if address:
        return address
    
    # Try to get from current user if authenticated
    try:
        current_user = await get_current_user(request)
        if current_user:
            return current_user
    except:
        pass
    
    return None

# Credit Report Endpoints
@app.post("/api/reports/generate")
async def generate_report(
    request: Request,
    report_type: str = "full",
    format: str = "pdf"
):
    """Generate credit report"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        from services.report_exporter import ReportExporter
        
        exporter = ReportExporter()
        
        if format == "pdf":
            result = await exporter.export_pdf(address, {"report_type": report_type})
        elif format == "json":
            result = await exporter.export_json(address, {"report_type": report_type})
        elif format == "csv":
            result = await exporter.export_csv(address, {"report_type": report_type})
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        # Save report to database
        from database.connection import get_session
        from database.models import CreditReport
        
        async with get_session() as session:
            report = CreditReport(
                wallet_address=address,
                report_type=report_type,
                format=format,
                file_path=result.get("file_path"),
                file_url=result.get("file_url"),
                metadata=result
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            
            result["report_id"] = report.id
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/reports/{report_id}/download")
async def download_report(report_id: int, request: Request):
    """Download report file"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        from database.connection import get_session
        from database.models import CreditReport
        from sqlalchemy import select
        
        async with get_session() as session:
            result = await session.execute(
                select(CreditReport).where(
                    CreditReport.id == report_id,
                    CreditReport.wallet_address == address
                )
            )
            report = result.scalar_one_or_none()
            
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            # Return report data
            return {
                "report_id": report.id,
                "format": report.format,
                "metadata": report.extra_metadata,
                "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/reports/{report_id}")
async def get_report(report_id: int, request: Request):
    """Get report metadata"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        from database.connection import get_session
        from database.models import CreditReport
        from sqlalchemy import select
        
        async with get_session() as session:
            result = await session.execute(
                select(CreditReport).where(
                    CreditReport.id == report_id,
                    CreditReport.wallet_address == address
                )
            )
            report = result.scalar_one_or_none()
            
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            return {
                "report_id": report.id,
                "report_type": report.report_type,
                "format": report.format,
                "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                "file_url": report.file_url,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/reports")
async def list_reports(request: Request, limit: int = 20):
    """List user's reports"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        from database.connection import get_session
        from database.models import CreditReport
        from sqlalchemy import select, desc
        
        async with get_session() as session:
            result = await session.execute(
                select(CreditReport)
                .where(CreditReport.wallet_address == address)
                .order_by(desc(CreditReport.generated_at))
                .limit(limit)
            )
            reports = result.scalars().all()
            
            return {
                "reports": [
                    {
                        "report_id": r.id,
                        "report_type": r.report_type,
                        "format": r.format,
                        "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                        "file_url": r.file_url,
                    }
                    for r in reports
                ]
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/reports/share")
async def share_report(request: Request):
    """Share report with protocol"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        data = await request.json()
        protocol_address = data.get("protocol_address")
        report_id = data.get("report_id")
        expires_in_days = data.get("expires_in_days", 30)
        
        if not protocol_address:
            raise HTTPException(status_code=400, detail="Protocol address required")
        
        from services.report_share import ReportShareManager
        
        manager = ReportShareManager()
        result = await manager.create_share_link(
            address, protocol_address, report_id, expires_in_days
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create share")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/reports/shared")
async def get_shared_reports(request: Request):
    """Get shared reports"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        from services.report_share import ReportShareManager
        
        manager = ReportShareManager()
        reports = await manager.get_shared_reports(address)
        
        return {"shared_reports": reports}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shared reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/reports/shared/{token}")
async def access_shared_report(token: str):
    """Access shared report via token"""
    try:
        from services.report_exporter import ReportExporter
        
        exporter = ReportExporter()
        share_info = await exporter.validate_share_token(token)
        
        if not share_info:
            raise HTTPException(status_code=404, detail="Invalid or expired share token")
        
        return share_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing shared report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/reports/share/{share_id}")
async def revoke_share(share_id: int, request: Request):
    """Revoke shared report access"""
    try:
        address = await get_wallet_address(request)
        if not address:
            raise HTTPException(status_code=401, detail="Wallet address required")
        
        from services.report_share import ReportShareManager
        
        manager = ReportShareManager()
        success = await manager.revoke_share(share_id, address)
        
        if not success:
            raise HTTPException(status_code=404, detail="Share not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking share: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints
@app.get("/api/analytics/breakdown/{address}")
async def get_score_breakdown(address: str, request: Request):
    """Get score breakdown"""
    try:
        from services.score_breakdown import ScoreBreakdownAnalyzer
        
        analyzer = ScoreBreakdownAnalyzer()
        breakdown = await analyzer.breakdown_score(address)
        
        return breakdown
    except Exception as e:
        logger.error(f"Error getting score breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/comparison/{address}")
async def get_wallet_comparison(address: str, request: Request, limit: int = 10):
    """Compare with similar wallets"""
    try:
        from services.wallet_comparator import WalletComparator
        
        comparator = WalletComparator()
        similar_wallets = await comparator.find_similar_wallets(address, limit=limit)
        comparison_metrics = await comparator.get_comparison_metrics(address, similar_wallets)
        percentile_rank = await comparator.get_percentile_rank(address)
        
        return {
            "address": address,
            "similar_wallets": similar_wallets,
            "comparison_metrics": comparison_metrics,
            "percentile_rank": percentile_rank,
        }
    except Exception as e:
        logger.error(f"Error getting wallet comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/benchmark/{address}")
async def get_benchmark_comparison(address: str, request: Request, industry: Optional[str] = None):
    """Compare to industry benchmark"""
    try:
        from services.benchmark_service import BenchmarkService
        
        benchmark_service = BenchmarkService()
        comparison = await benchmark_service.compare_to_benchmark(address, industry)
        
        return comparison
    except Exception as e:
        logger.error(f"Error getting benchmark comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/comprehensive/{address}")
async def get_comprehensive_analytics(address: str, request: Request):
    """Get comprehensive analytics"""
    try:
        from services.analytics_engine import AnalyticsEngine
        from datetime import datetime
        
        engine = AnalyticsEngine()
        analytics = await engine.get_comprehensive_analytics(address)
        analytics["generated_at"] = datetime.utcnow().isoformat()
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/insights/{address}")
async def get_analytics_insights(address: str, request: Request):
    """Get insights and recommendations"""
    try:
        from services.analytics_engine import AnalyticsEngine
        
        engine = AnalyticsEngine()
        insights = await engine.generate_insights(address)
        recommendations = await engine.get_recommendations(address)
        
        return {
            "address": address,
            "insights": insights,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"Error getting analytics insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ========== Public API Endpoints (v1) ==========

from middleware.api_auth import require_api_key, get_api_key

@app.get("/api/v1/score/{address}")
@limiter.limit("100/minute")
async def get_public_score(
    address: str,
    request: Request,
    api_key: APIAccess = Depends(require_api_key)
):
    """Get credit score via public API"""
    try:
        from services.scoring import ScoringService
        
        scoring_service = ScoringService()
        result = await scoring_service.compute_score(address)
        
        return {
            "address": address,
            "score": result.get("score", 0),
            "risk_band": result.get("riskBand", 0),
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting public score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/score/{address}/history")
@limiter.limit("100/minute")
async def get_public_score_history(
    address: str,
    request: Request,
    limit: int = 30,
    api_key: APIAccess = Depends(require_api_key)
):
    """Get score history via public API"""
    try:
        from database.connection import get_db_session
        from database.models import ScoreHistory
        from sqlalchemy import select, desc
        
        async with get_db_session() as session:
            result = await session.execute(
                select(ScoreHistory)
                .where(ScoreHistory.wallet_address == address)
                .order_by(desc(ScoreHistory.computed_at))
                .limit(limit)
            )
            history = result.scalars().all()
            
            return {
                "address": address,
                "history": [
                    {
                        "score": h.score,
                        "risk_band": h.risk_band,
                        "computed_at": h.computed_at.isoformat() if h.computed_at else None,
                    }
                    for h in history
                ],
            }
    except Exception as e:
        logger.error(f"Error getting public score history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/loans/{address}")
@limiter.limit("100/minute")
async def get_public_loans(
    address: str,
    request: Request,
    api_key: APIAccess = Depends(require_api_key)
):
    """Get user loans via public API"""
    try:
        from services.loan_service import LoanService
        
        loan_service = LoanService()
        loans = await loan_service.get_loans_by_user(address)
        
        return {
            "address": address,
            "loans": loans,
        }
    except Exception as e:
        logger.error(f"Error getting public loans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/portfolio/{address}")
@limiter.limit("100/minute")
async def get_public_portfolio(
    address: str,
    request: Request,
    api_key: APIAccess = Depends(require_api_key)
):
    """Get portfolio data via public API"""
    try:
        from services.portfolio_service import PortfolioService
        
        portfolio_service = PortfolioService()
        portfolio_value = await portfolio_service.get_total_portfolio_value(address)
        token_holdings = await portfolio_service.get_token_holdings(address)
        
        return {
            "address": address,
            "total_value": portfolio_value,
            "holdings": token_holdings,
        }
    except Exception as e:
        logger.error(f"Error getting public portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/webhooks")
@limiter.limit("10/minute")
async def register_webhook(
    request: Request,
    api_key: APIAccess = Depends(require_api_key)
):
    """Register webhook"""
    try:
        data = await request.json()
        url = data.get("url")
        events = data.get("events", [])
        
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        if not events:
            raise HTTPException(status_code=400, detail="At least one event is required")
        
        from services.webhook_service import WebhookService
        
        webhook_service = WebhookService()
        webhook = await webhook_service.register_webhook(api_key.id, url, events)
        
        if not webhook:
            raise HTTPException(status_code=500, detail="Failed to register webhook")
        
        return webhook
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/webhooks/{webhook_id}")
@limiter.limit("10/minute")
async def delete_webhook(
    webhook_id: int,
    request: Request,
    api_key: APIAccess = Depends(require_api_key)
):
    """Delete webhook"""
    try:
        from database.connection import get_db_session
        from database.models import Webhook
        from sqlalchemy import select
        
        async with get_db_session() as session:
            result = await session.execute(
                select(Webhook).where(
                    Webhook.id == webhook_id,
                    Webhook.api_key_id == api_key.id
                )
            )
            webhook = result.scalar_one_or_none()
            
            if not webhook:
                raise HTTPException(status_code=404, detail="Webhook not found")
            
            await session.delete(webhook)
            await session.commit()
            
            return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Add rate limit exception handler
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


