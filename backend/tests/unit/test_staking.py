"""
Unit tests for StakingService
"""
import pytest
from unittest.mock import Mock, patch
from services.staking import StakingService


@pytest.mark.unit
class TestStakingService:
    """Test StakingService"""
    
    @pytest.fixture
    def staking_service_with_contract(self):
        """Create StakingService with contract"""
        with patch('services.staking.Web3') as mock_web3_class:
            mock_w3 = Mock()
            mock_contract = Mock()
            mock_contract.functions = Mock()
            mock_contract.functions.stakedAmount = Mock(return_value=Mock(call=Mock(return_value=5000000000000000000)))
            mock_contract.functions.integrationTier = Mock(return_value=Mock(call=Mock(return_value=2)))
            mock_w3.eth.contract.return_value = mock_contract
            mock_web3_class.return_value = mock_w3
            
            with patch.dict('os.environ', {
                'QIE_TESTNET_RPC_URL': 'https://testnet.qie.digital',
                'STAKING_ADDRESS': '0x' + '1' * 40,
            }):
                service = StakingService()
                service.w3 = mock_w3
                service.staking_contract = mock_contract
                yield service
    
    @pytest.fixture
    def staking_service_without_contract(self):
        """Create StakingService without contract (optional staking)"""
        with patch('services.staking.Web3') as mock_web3_class:
            mock_w3 = Mock()
            mock_web3_class.return_value = mock_w3
            
            with patch.dict('os.environ', {
                'QIE_TESTNET_RPC_URL': 'https://testnet.qie.digital',
                'STAKING_ADDRESS': '',  # Not configured
            }):
                service = StakingService()
                service.w3 = mock_w3
                yield service
    
    def test_get_staked_amount_success(self, staking_service_with_contract):
        """Test successful staked amount retrieval"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        amount = staking_service_with_contract.get_staked_amount(address)
        
        assert amount == 5000000000000000000
    
    def test_get_staked_amount_no_contract(self, staking_service_without_contract):
        """Test staked amount when contract not configured"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        amount = staking_service_without_contract.get_staked_amount(address)
        
        assert amount == 0
    
    def test_get_staked_amount_error(self, staking_service_with_contract):
        """Test staked amount error handling"""
        staking_service_with_contract.staking_contract.functions.stakedAmount.side_effect = Exception("Contract error")
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        amount = staking_service_with_contract.get_staked_amount(address)
        
        assert amount == 0
    
    def test_get_integration_tier_success(self, staking_service_with_contract):
        """Test successful tier retrieval"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        tier = staking_service_with_contract.get_integration_tier(address)
        
        assert tier == 2
    
    def test_get_integration_tier_no_contract(self, staking_service_without_contract):
        """Test tier when contract not configured"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        tier = staking_service_without_contract.get_integration_tier(address)
        
        assert tier == 0
    
    def test_get_integration_tier_error(self, staking_service_with_contract):
        """Test tier error handling"""
        staking_service_with_contract.staking_contract.functions.integrationTier.side_effect = Exception("Contract error")
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        tier = staking_service_with_contract.get_integration_tier(address)
        
        assert tier == 0
    
    def test_calculate_staking_boost_tier_0(self, staking_service_with_contract):
        """Test staking boost for tier 0"""
        boost = staking_service_with_contract.calculate_staking_boost(0)
        assert boost == 0
    
    def test_calculate_staking_boost_tier_1(self, staking_service_with_contract):
        """Test staking boost for tier 1 (Bronze)"""
        boost = staking_service_with_contract.calculate_staking_boost(1)
        assert boost == 50
    
    def test_calculate_staking_boost_tier_2(self, staking_service_with_contract):
        """Test staking boost for tier 2 (Silver)"""
        boost = staking_service_with_contract.calculate_staking_boost(2)
        assert boost == 150
    
    def test_calculate_staking_boost_tier_3(self, staking_service_with_contract):
        """Test staking boost for tier 3 (Gold)"""
        boost = staking_service_with_contract.calculate_staking_boost(3)
        assert boost == 300
    
    def test_calculate_staking_boost_invalid_tier(self, staking_service_with_contract):
        """Test staking boost for invalid tier"""
        boost = staking_service_with_contract.calculate_staking_boost(99)
        assert boost == 0
    
    def test_get_staking_abi(self, staking_service_with_contract):
        """Test staking ABI retrieval"""
        abi = staking_service_with_contract._get_staking_abi()
        
        assert isinstance(abi, list)
        assert len(abi) > 0
        # Check for required functions
        function_names = [func.get('name') for func in abi if isinstance(func, dict)]
        assert 'integrationTier' in function_names
        assert 'stakedAmount' in function_names

