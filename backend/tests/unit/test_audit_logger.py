"""
Unit tests for audit logging
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.audit_logger import (
    get_client_ip,
    log_audit_event,
    log_score_generation,
    log_on_chain_update,
    log_loan_creation,
    log_admin_action
)
from fastapi import Request


@pytest.mark.unit
class TestAuditLogger:
    """Test audit logging functions"""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request"""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/score"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        return request
    
    def test_get_client_ip_direct(self, mock_request):
        """Test getting client IP directly"""
        ip = get_client_ip(mock_request)
        assert ip == "127.0.0.1"
    
    def test_get_client_ip_forwarded(self, mock_request):
        """Test getting client IP from X-Forwarded-For"""
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_real_ip(self, mock_request):
        """Test getting client IP from X-Real-IP"""
        mock_request.headers = {"X-Real-IP": "192.168.1.2"}
        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.2"
    
    def test_get_client_ip_priority(self, mock_request):
        """Test that X-Forwarded-For takes priority over X-Real-IP"""
        mock_request.headers = {
            "X-Forwarded-For": "192.168.1.1",
            "X-Real-IP": "192.168.1.2"
        }
        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_no_client(self, mock_request):
        """Test getting client IP when client is None"""
        mock_request.client = None
        ip = get_client_ip(mock_request)
        assert ip is None
    
    def test_log_audit_event_success(self, mock_request):
        """Test logging successful audit event"""
        with patch('utils.audit_logger.audit_logger') as mock_logger:
            log_audit_event(
                request=mock_request,
                action="test_action",
                result="success",
                user_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            )
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "test_action" in call_args[0][0]
            assert call_args[1]['extra']['action'] == "test_action"
            assert call_args[1]['extra']['result'] == "success"
    
    def test_log_audit_event_failure(self, mock_request):
        """Test logging failed audit event"""
        with patch('utils.audit_logger.audit_logger') as mock_logger:
            log_audit_event(
                request=mock_request,
                action="test_action",
                result="failure",
                error_message="Test error"
            )
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[1]['extra']['error_message'] == "Test error"
    
    def test_log_audit_event_with_metadata(self, mock_request):
        """Test logging audit event with metadata"""
        with patch('utils.audit_logger.audit_logger') as mock_logger:
            metadata = {"key": "value", "number": 123}
            log_audit_event(
                request=mock_request,
                action="test_action",
                result="success",
                metadata=metadata
            )
            
            call_args = mock_logger.info.call_args
            assert call_args[1]['extra']['metadata'] == metadata
    
    def test_log_audit_event_user_from_state(self, mock_request):
        """Test logging audit event with user from request state"""
        mock_request.state.user_address = "0x1234567890123456789012345678901234567890"
        
        with patch('utils.audit_logger.audit_logger') as mock_logger:
            log_audit_event(
                request=mock_request,
                action="test_action",
                result="success"
            )
            
            call_args = mock_logger.info.call_args
            assert call_args[1]['extra']['user_address'] == "0x1234567890123456789012345678901234567890"
    
    def test_log_score_generation(self, mock_request):
        """Test logging score generation"""
        with patch('utils.audit_logger.log_audit_event') as mock_log:
            log_score_generation(
                request=mock_request,
                address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                score=750,
                result="success"
            )
            
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['action'] == "generate_score"
            assert call_kwargs['user_address'] == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            assert call_kwargs['metadata']['score'] == 750
    
    def test_log_score_generation_with_error(self, mock_request):
        """Test logging score generation with error"""
        with patch('utils.audit_logger.log_audit_event') as mock_log:
            log_score_generation(
                request=mock_request,
                address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                score=0,
                result="failure",
                error="Network error"
            )
            
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['error_message'] == "Network error"
    
    def test_log_on_chain_update(self, mock_request):
        """Test logging on-chain update"""
        with patch('utils.audit_logger.log_audit_event') as mock_log:
            log_on_chain_update(
                request=mock_request,
                address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                tx_hash="0x1234567890abcdef",
                result="success"
            )
            
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['action'] == "update_on_chain"
            assert call_kwargs['metadata']['tx_hash'] == "0x1234567890abcdef"
    
    def test_log_loan_creation(self, mock_request):
        """Test logging loan creation"""
        with patch('utils.audit_logger.log_audit_event') as mock_log:
            log_loan_creation(
                request=mock_request,
                address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                loan_id=123,
                result="success"
            )
            
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['action'] == "create_loan"
            assert call_kwargs['metadata']['loan_id'] == 123
    
    def test_log_admin_action(self, mock_request):
        """Test logging admin action"""
        with patch('utils.audit_logger.log_audit_event') as mock_log:
            metadata = {"action_type": "update_config"}
            log_admin_action(
                request=mock_request,
                action="update_config",
                result="success",
                metadata=metadata
            )
            
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs['action'] == "admin_update_config"
            assert call_kwargs['metadata'] == metadata

