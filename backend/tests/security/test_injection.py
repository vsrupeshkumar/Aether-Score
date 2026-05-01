"""
Security tests for injection attacks
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app import app


@pytest.fixture
async def client():
    """Create async test client"""
    from httpx import AsyncClient
    async with AsyncClient(base_url="http://test", app=app) as ac:
        yield ac


@pytest.mark.security
class TestInjection:
    """Test injection attack prevention"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_address(self, client):
        """Test SQL injection in address parameter"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
        ]
        
        for malicious in malicious_inputs:
            # Address validation should reject these
            response = await client.get(f"/api/score/{malicious}")
            # Should return 422 (validation error) or 400, not 500
            assert response.status_code in [400, 422, 404]
    
    @pytest.mark.asyncio
    async def test_xss_in_chat_message(self, client):
        """Test XSS in chat message"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='evil.com'></iframe>",
        ]
        
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            for payload in xss_payloads:
                response = await client.post(
                    "/api/chat",
                    json={
                        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                        "message": payload
                    }
                )
                
                # Should sanitize and accept (200) or reject (422)
                if response.status_code == 200:
                    # Check that response doesn't contain raw payload
                    data = response.json()
                    assert "<script>" not in str(data).lower()
                    assert "javascript:" not in str(data).lower()
    
    @pytest.mark.asyncio
    async def test_command_injection(self, client):
        """Test command injection attempts"""
        malicious_inputs = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(id)",
        ]
        
        for malicious in malicious_inputs:
            response = await client.post(
                "/api/score",
                json={"address": f"0x{malicious}"}
            )
            # Should be rejected by validation
            assert response.status_code in [400, 422, 401]

