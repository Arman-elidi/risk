"""
Integration tests for portfolio API endpoints
"""
import pytest
from app.db.models import Portfolio


@pytest.mark.integration
@pytest.mark.api
class TestPortfolioAPI:
    """Test portfolio CRUD operations"""
    
    async def test_create_portfolio(self, client, auth_headers, sample_portfolio_data):
        """Test creating a new portfolio"""
        response = await client.post(
            "/api/v1/portfolios",
            json=sample_portfolio_data,
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["portfolio_name"] == sample_portfolio_data["portfolio_name"]
        assert data["base_currency"] == sample_portfolio_data["base_currency"]
        assert "portfolio_id" in data
    
    async def test_list_portfolios(self, client, auth_headers, db_session):
        """Test listing portfolios"""
        # Create test portfolios
        portfolio1 = Portfolio(
            portfolio_name="Portfolio A",
            entity_id=1,
            base_currency="USD",
            is_active=True,
        )
        portfolio2 = Portfolio(
            portfolio_name="Portfolio B",
            entity_id=1,
            base_currency="EUR",
            is_active=True,
        )
        db_session.add_all([portfolio1, portfolio2])
        await db_session.commit()
        
        response = await client.get("/api/v1/portfolios", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    async def test_get_portfolio_by_id(self, client, auth_headers, db_session):
        """Test retrieving specific portfolio"""
        portfolio = Portfolio(
            portfolio_name="Test Portfolio",
            entity_id=1,
            base_currency="USD",
            is_active=True,
        )
        db_session.add(portfolio)
        await db_session.commit()
        await db_session.refresh(portfolio)
        
        response = await client.get(
            f"/api/v1/portfolios/{portfolio.portfolio_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_id"] == portfolio.portfolio_id
        assert data["portfolio_name"] == "Test Portfolio"
    
    async def test_get_nonexistent_portfolio(self, client, auth_headers):
        """Test retrieving non-existent portfolio"""
        response = await client.get(
            "/api/v1/portfolios/999999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
    
    async def test_unauthorized_access(self, client):
        """Test accessing portfolio without auth"""
        response = await client.get("/api/v1/portfolios")
        
        assert response.status_code == 403  # No auth header
