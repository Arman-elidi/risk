"""
Pytest fixtures for testing
"""
import pytest
import asyncio
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient

from app.main import app
from app.db.models import Base
from app.db.session import get_db
from app.core.auth import create_access_token


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://riskuser:password@localhost:5432/risk_orchestrator_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """Create test HTTP client"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Generate auth headers for testing"""
    token = create_access_token({
        "sub": "1",
        "username": "test_user",
        "role": "ADMIN",
        "scopes": ["read", "write"],
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing"""
    return {
        "portfolio_name": "Test Portfolio",
        "entity_id": 1,
        "base_currency": "USD",
        "is_active": True,
    }


@pytest.fixture
def sample_bond_position():
    """Sample bond position for testing"""
    return {
        "isin": "US912828Z230",
        "notional": 1000000.0,
        "clean_price": 98.5,
        "coupon_rate": 0.025,
        "maturity_date": date(2030, 12, 31),
        "issue_date": date(2020, 1, 1),
        "coupon_frequency": 2,
    }


@pytest.fixture
def sample_risk_snapshot():
    """Sample risk snapshot for testing"""
    return {
        "portfolio_id": 1,
        "snapshot_date": date.today(),
        "calculation_timestamp": datetime.utcnow(),
        "calculation_status": "SUCCESS",
        "var_1d_95": 50000.0,
        "stressed_var": 75000.0,
        "dv01_total": 1500.0,
        "duration": 5.2,
        "convexity": 28.5,
    }
