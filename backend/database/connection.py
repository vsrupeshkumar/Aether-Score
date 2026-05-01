"""
Database connection and session management with connection pooling
"""
import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text
from contextlib import asynccontextmanager
from utils.logger import get_logger

logger = get_logger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://")

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

# Global engine and session factory
engine = None
async_session_maker: Optional[async_sessionmaker] = None


def get_engine():
    """Get or create database engine with connection pooling"""
    global engine
    
    if engine is None:
        if not DATABASE_URL:
            logger.warning("DATABASE_URL not set, database features disabled")
            return None
        
        engine = create_async_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            future=True,
        )
        
        # Add connection pool event listeners
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Set connection-level settings"""
            pass  # PostgreSQL doesn't need pragma
        
        logger.info(
            "Database engine created",
            extra={
                "pool_size": POOL_SIZE,
                "max_overflow": MAX_OVERFLOW,
                "pool_timeout": POOL_TIMEOUT,
            }
        )
    
    return engine


def get_session_maker():
    """Get or create async session maker"""
    global async_session_maker
    
    if async_session_maker is None:
        engine = get_engine()
        if engine is None:
            return None
        
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    
    return async_session_maker


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic cleanup
    
    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)
    """
    session_maker = get_session_maker()
    if session_maker is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_pool():
    """Get database connection pool for direct access"""
    engine = get_engine()
    if engine is None:
        return None
    return engine.pool


async def init_db():
    """
    Initialize database: create tables and indexes
    
    This should be called once at application startup
    """
    engine = get_engine()
    if engine is None:
        logger.warning("Database not configured, skipping initialization")
        return
    
    try:
        from .models import Base
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", exc_info=True, extra={"error": str(e)})
        raise


async def check_db_health() -> dict:
    """Check database connection health"""
    engine = get_engine()
    if engine is None:
        return {
            "status": "not_configured",
            "message": "Database not configured"
        }
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        
        pool = engine.pool
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except Exception as e:
        logger.error("Database health check failed", exc_info=True, extra={"error": str(e)})
        return {
            "status": "unhealthy",
            "error": str(e)
        }

