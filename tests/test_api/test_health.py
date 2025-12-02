"""
Integration tests for health and monitoring endpoints
"""
import pytest


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    async def test_health_check(self, client):
        """Test basic health check"""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "risk-orchestrator"
        assert data["version"] == "2.1.0"
    
    async def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe"""
        response = await client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True
    
    async def test_readiness_probe(self, client):
        """Test Kubernetes readiness probe"""
        response = await client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert "database" in data["checks"]
    
    async def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = await client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        # Prometheus text format
        assert response.headers["content-type"].startswith("text/plain")
        
        content = response.text
        # Check for key metrics
        assert "http_requests_total" in content
        assert "risk_orchestrator_info" in content
