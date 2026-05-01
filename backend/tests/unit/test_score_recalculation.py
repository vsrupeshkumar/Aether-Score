"""
Unit tests for ScoreRecalculationService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.score_recalculation import ScoreRecalculationService


@pytest.mark.unit
class TestScoreRecalculationService:
    """Test ScoreRecalculationService"""
    
    @pytest.fixture
    def recalculation_service(self):
        """Create ScoreRecalculationService instance"""
        with patch('services.score_recalculation.MLScoringService') as mock_scoring, \
             patch('services.score_recalculation.TransactionIndexer') as mock_indexer, \
             patch('services.score_recalculation.Redis') as mock_redis, \
             patch('services.score_recalculation.Queue') as mock_queue:
            
            mock_scoring_instance = Mock()
            mock_scoring_instance.compute_score = AsyncMock(return_value={
                "score": 750,
                "riskBand": 1
            })
            mock_scoring.return_value = mock_scoring_instance
            
            mock_indexer_instance = Mock()
            mock_indexer_instance.index_address_transactions = AsyncMock()
            mock_indexer.return_value = mock_indexer_instance
            
            mock_redis_instance = Mock()
            mock_redis.from_url.return_value = mock_redis_instance
            
            mock_queue_instance = Mock()
            mock_queue.return_value = mock_queue_instance
            
            service = ScoreRecalculationService()
            service.ml_scoring_service = mock_scoring_instance
            service.transaction_indexer = mock_indexer_instance
            service.redis_conn = mock_redis_instance
            service.queue = mock_queue_instance
            yield service
    
    @pytest.mark.asyncio
    async def test_recalculate_single_score(self, recalculation_service):
        """Test recalculating score for single address"""
        with patch('services.score_recalculation.get_db_session') as mock_session, \
             patch('services.score_recalculation.UserRepository') as mock_user_repo:
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_user_repo.get_or_create_user = AsyncMock()
            
            result = await recalculation_service.recalculate_single_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert "score" in result
            assert result["score"] >= 0
            assert result["score"] <= 1000
    
    @pytest.mark.asyncio
    async def test_batch_recalculate(self, recalculation_service):
        """Test batch score recalculation"""
        with patch('services.score_recalculation.get_db_session') as mock_session, \
             patch('services.score_recalculation.UserRepository') as mock_user_repo:
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            
            mock_user = Mock()
            mock_user.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            mock_user_repo.get_all_users = AsyncMock(return_value=[mock_user])
            
            with patch.object(recalculation_service, '_should_recalculate', new_callable=AsyncMock) as mock_should:
                mock_should.return_value = True
                
                result = await recalculation_service.batch_recalculate(limit=10)
                
                assert result["status"] == "completed"
                assert "queued_for_recalculation" in result
    
    @pytest.mark.asyncio
    async def test_should_recalculate_new_user(self, recalculation_service):
        """Test should recalculate for new user"""
        with patch('services.score_recalculation.get_db_session') as mock_session, \
             patch('services.score_recalculation.ScoreRepository') as mock_score_repo:
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_score_repo.get_score = AsyncMock(return_value=None)  # No existing score
            
            should_recalc = await recalculation_service._should_recalculate(
                mock_session_obj,
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            )
            
            assert should_recalc is True
    
    @pytest.mark.asyncio
    async def test_should_recalculate_old_score(self, recalculation_service):
        """Test should recalculate for old score"""
        from datetime import datetime, timedelta
        
        with patch('services.score_recalculation.get_db_session') as mock_session, \
             patch('services.score_recalculation.ScoreRepository') as mock_score_repo:
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            
            mock_score = Mock()
            mock_score.last_updated = datetime.now() - timedelta(days=2)  # 2 days old
            mock_score_repo.get_score = AsyncMock(return_value=mock_score)
            
            recalculation_service.recalculation_interval_hours = 24  # 1 day interval
            
            should_recalc = await recalculation_service._should_recalculate(
                mock_session_obj,
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            )
            
            assert should_recalc is True
    
    @pytest.mark.asyncio
    async def test_should_recalculate_recent_score(self, recalculation_service):
        """Test should not recalculate for recent score"""
        from datetime import datetime, timedelta
        
        with patch('services.score_recalculation.get_db_session') as mock_session, \
             patch('services.score_recalculation.ScoreRepository') as mock_score_repo, \
             patch('services.score_recalculation.TransactionIndexer') as mock_indexer:
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            
            mock_score = Mock()
            mock_score.last_updated = datetime.now() - timedelta(hours=1)  # 1 hour old
            mock_score_repo.get_score = AsyncMock(return_value=mock_score)
            
            mock_indexer_instance = Mock()
            mock_indexer_instance._get_last_indexed_transaction = AsyncMock(return_value=None)
            recalculation_service.transaction_indexer = mock_indexer_instance
            
            recalculation_service.recalculation_interval_hours = 24  # 1 day interval
            
            should_recalc = await recalculation_service._should_recalculate(
                mock_session_obj,
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            )
            
            assert should_recalc is False

