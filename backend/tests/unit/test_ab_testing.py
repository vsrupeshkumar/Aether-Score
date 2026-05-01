"""
Unit tests for ABTestingService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from services.ab_testing import ABTestingService
from database.models import ABExperiment, ABAllocation, ABMetric


@pytest.mark.unit
class TestABTestingService:
    """Test ABTestingService"""
    
    @pytest.fixture
    def ab_service(self):
        """Create ABTestingService instance"""
        return ABTestingService()
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, ab_service, mock_session):
        """Test creating A/B experiment"""
        with patch('services.ab_testing.ABExperimentRepository') as mock_repo:
            mock_repo.get_experiment_by_name = AsyncMock(return_value=None)
            mock_repo.create_experiment = AsyncMock(return_value=Mock(id=1, experiment_name="test_exp"))
            
            result = await ab_service.create_experiment(
                experiment_name="test_exp",
                variant_a_name="rule_based",
                variant_b_name="ml_model",
                allocation_ratio=0.5
            )
            
            assert result["status"] == "success"
            assert "experiment_id" in result
    
    @pytest.mark.asyncio
    async def test_create_experiment_duplicate(self, ab_service, mock_session):
        """Test creating duplicate experiment"""
        with patch('services.ab_testing.ABExperimentRepository') as mock_repo:
            existing_exp = Mock()
            existing_exp.experiment_name = "test_exp"
            mock_repo.get_experiment_by_name = AsyncMock(return_value=existing_exp)
            
            result = await ab_service.create_experiment(
                experiment_name="test_exp",
                variant_a_name="rule_based",
                variant_b_name="ml_model"
            )
            
            assert result["status"] == "error"
            assert "already exists" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_or_allocate_variant_new_user(self, ab_service):
        """Test allocating new user to variant"""
        with patch('services.ab_testing.ABExperimentRepository') as mock_exp_repo, \
             patch('services.ab_testing.ABAllocationRepository') as mock_alloc_repo:
            
            experiment = Mock()
            experiment.id = 1
            experiment.status = "active"
            experiment.allocation_ratio = Decimal("0.5")
            mock_exp_repo.get_experiment_by_name = AsyncMock(return_value=experiment)
            
            mock_alloc_repo.get_allocation = AsyncMock(return_value=None)
            mock_alloc_repo.create_allocation = AsyncMock(return_value=Mock(variant="A"))
            
            result = await ab_service.get_or_allocate_variant("test_exp", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result["status"] == "success"
            assert result["variant"] in ["A", "B"]
    
    @pytest.mark.asyncio
    async def test_get_or_allocate_variant_existing_user(self, ab_service):
        """Test getting existing user's variant"""
        with patch('services.ab_testing.ABExperimentRepository') as mock_exp_repo, \
             patch('services.ab_testing.ABAllocationRepository') as mock_alloc_repo:
            
            experiment = Mock()
            experiment.id = 1
            experiment.status = "active"
            mock_exp_repo.get_experiment_by_name = AsyncMock(return_value=experiment)
            
            allocation = Mock()
            allocation.variant = "B"
            allocation.allocated_at = Mock()
            allocation.allocated_at.isoformat = Mock(return_value="2024-01-01T00:00:00")
            mock_alloc_repo.get_allocation = AsyncMock(return_value=allocation)
            
            result = await ab_service.get_or_allocate_variant("test_exp", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result["status"] == "success"
            assert result["variant"] == "B"
    
    @pytest.mark.asyncio
    async def test_record_metric(self, ab_service):
        """Test recording metric for experiment"""
        with patch('services.ab_testing.ABExperimentRepository') as mock_exp_repo, \
             patch('services.ab_testing.ABAllocationRepository') as mock_alloc_repo, \
             patch('services.ab_testing.ABMetricRepository') as mock_metric_repo:
            
            experiment = Mock()
            experiment.id = 1
            mock_exp_repo.get_experiment_by_name = AsyncMock(return_value=experiment)
            
            allocation = Mock()
            allocation.variant = "A"
            mock_alloc_repo.get_allocation = AsyncMock(return_value=allocation)
            
            mock_metric_repo.create_metric = AsyncMock(return_value=Mock(id=1))
            
            result = await ab_service.record_metric(
                "test_exp",
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "default_rate",
                metric_value=0.05
            )
            
            assert result["status"] == "success"
            assert "metric_id" in result
    
    @pytest.mark.asyncio
    async def test_analyze_experiment_results(self, ab_service):
        """Test analyzing experiment results"""
        with patch('services.ab_testing.ABExperimentRepository') as mock_exp_repo, \
             patch('services.ab_testing.ABMetricRepository') as mock_metric_repo:
            
            experiment = Mock()
            experiment.id = 1
            experiment.experiment_name = "test_exp"
            experiment.status = "active"
            experiment.variant_a_name = "rule_based"
            experiment.variant_b_name = "ml_model"
            mock_exp_repo.get_experiment_by_name = AsyncMock(return_value=experiment)
            
            # Mock metrics
            metric_a = Mock()
            metric_a.variant = "A"
            metric_a.wallet_address = "0x" + "1" * 40
            metric_a.metric_name = "default_rate"
            metric_a.metric_value = Decimal("0.05")
            
            metric_b = Mock()
            metric_b.variant = "B"
            metric_b.wallet_address = "0x" + "2" * 40
            metric_b.metric_name = "default_rate"
            metric_b.metric_value = Decimal("0.03")
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [metric_a, metric_b]
            mock_metric_repo.get_metrics = AsyncMock(return_value=[metric_a, metric_b])
            
            result = await ab_service.analyze_experiment_results("test_exp")
            
            assert result["status"] == "success"
            assert "results" in result
            assert "variant_a" in result["results"]
            assert "variant_b" in result["results"]

