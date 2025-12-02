#!/bin/bash
# Run all tests locally before committing

set -e

echo "=== Running Risk Orchestrator Test Suite ==="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if test database is running
echo -e "\n${GREEN}[1/5] Checking PostgreSQL...${NC}"
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${RED}PostgreSQL is not running. Start it with:${NC}"
    echo "  docker run -d -p 5432:5432 -e POSTGRES_DB=risk_orchestrator_test -e POSTGRES_USER=riskuser -e POSTGRES_PASSWORD=testpass postgres:15"
    exit 1
fi

# Check Redis
echo -e "\n${GREEN}[2/5] Checking Redis...${NC}"
if ! redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    echo -e "${RED}Redis is not running. Start it with:${NC}"
    echo "  docker run -d -p 6379:6379 redis:7-alpine"
    exit 1
fi

# Install dependencies
echo -e "\n${GREEN}[3/5] Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -e risk-core/

# Run linting
echo -e "\n${GREEN}[4/5] Running linting...${NC}"
echo "  - flake8..."
flake8 app/ risk-core/ --max-line-length=120 --exclude=__pycache__ --quiet || true
echo "  - black..."
black --check app/ risk-core/ --quiet || true
echo "  - isort..."
isort --check-only app/ risk-core/ --quiet || true

# Run tests
echo -e "\n${GREEN}[5/5] Running tests...${NC}"

# Unit tests (fast)
echo -e "\n  ${GREEN}Unit tests...${NC}"
pytest tests/test_risk_core/ -v -m unit --tb=short

# Integration tests (slower)
echo -e "\n  ${GREEN}Integration tests...${NC}"
export DATABASE_URL=postgresql+asyncpg://riskuser:testpass@localhost:5432/risk_orchestrator_test
export SECRET_KEY=test-secret-key
export REDIS_URL=redis://localhost:6379/0

pytest tests/test_api/ tests/test_services/ -v -m integration --tb=short

# Coverage report
echo -e "\n  ${GREEN}Coverage report...${NC}"
pytest tests/ --cov=app --cov=risk_core --cov-report=term-missing --cov-fail-under=70

echo -e "\n${GREEN}✅ All tests passed!${NC}"
