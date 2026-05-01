"""
Load testing for API endpoints
Uses locust for load testing
"""
from locust import HttpUser, task, between
import random


class AETHER-SCOREUser(HttpUser):
    """Simulated user for load testing"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        # Could set up authentication here
        self.api_key = None  # Would use actual API key in real test
    
    @task(3)
    def get_health(self):
        """Health check endpoint (most common)"""
        self.client.get("/health")
    
    @task(2)
    def get_score(self):
        """Get score for random address"""
        # Use test addresses
        addresses = [
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            "0x8ba1f109551bD432803012645Hac136c22C1729",
            "0x1234567890123456789012345678901234567890",
        ]
        address = random.choice(addresses)
        self.client.get(f"/api/score/{address}")
    
    @task(1)
    def generate_score(self):
        """Generate new score (less frequent, more expensive)"""
        # This would require authentication in real scenario
        # For load test, we'll just test the endpoint structure
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        # Note: This would fail without auth, but tests endpoint availability
        self.client.post(
            "/api/score",
            json={"address": address},
            catch_response=True
        )
    
    @task(1)
    def get_staking_info(self):
        """Get staking information"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        self.client.get(f"/api/staking/{address}")
    
    @task(1)
    def get_oracle_price(self):
        """Get oracle price"""
        self.client.get("/api/oracle/price")


# Run with: locust -f tests/load/test_api_load.py --host=http://localhost:8000
# Then open http://localhost:8089 to start the test


