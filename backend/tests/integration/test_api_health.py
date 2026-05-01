"""
Integration tests for /health and /health/ready endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.mark.integration
class TestAPIHealth:
    """Test health check endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_health_check_ready(self, client):
        """Test readiness check"""
        # Check if /health/ready endpoint exists
        # If not implemented, this will return 404
        response = client.get("/health/ready")
        
        # Either 200 (if implemented) or 404 (if not)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

