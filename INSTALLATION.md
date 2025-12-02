# AI Risk Orchestrator - Installation & User Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Local Development Setup](#local-development-setup)
3. [Database Setup](#database-setup)
4. [Dify AI Integration](#dify-ai-integration)
5. [Running the Application](#running-the-application)
6. [User Guide](#user-guide)
7. [API Documentation](#api-documentation)
8. [Troubleshooting](#troubleshooting)

---

## 1. System Requirements

### Minimum Hardware
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD

### Software Dependencies
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+ (optional, for caching)
- **Node.js**: 18+ (for frontend)
- **Docker**: 24+ (for containerized deployment)

---

## 2. Local Development Setup

### Step 1: Clone Repository

```bash
cd ~/Documents
git clone <your-repo-url> RISK
cd RISK
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install risk-core library
pip install -e risk-core/
```

### Step 4: Install Frontend Dependencies

```bash
cd risk-frontend
npm install
cd ..
```

---

## 3. Database Setup

### Option A: Using Docker (Recommended)

```bash
# Start PostgreSQL
docker run -d \
  --name risk-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=risk_orchestrator \
  -e POSTGRES_USER=riskuser \
  -e POSTGRES_PASSWORD=your_secure_password \
  -v risk_postgres_data:/var/lib/postgresql/data \
  postgres:15

# Start Redis (optional)
docker run -d \
  --name risk-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Option B: Manual PostgreSQL Installation

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb risk_orchestrator
createuser riskuser -P  # Enter password when prompted
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-15
sudo systemctl start postgresql

# Create user and database
sudo -u postgres psql
postgres=# CREATE USER riskuser WITH PASSWORD 'your_secure_password';
postgres=# CREATE DATABASE risk_orchestrator OWNER riskuser;
postgres=# \q
```

### Step 5: Configure Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit .env file
nano .env
```

**Required settings in `.env`:**

```bash
# Security (REQUIRED)
SECRET_KEY=your-256-bit-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://riskuser:your_secure_password@localhost:5432/risk_orchestrator

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Dify AI (see section 4)
DIFY_API_URL=http://localhost:3001/v1
DIFY_API_KEY=your-dify-api-key

# Email/SMS (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Step 6: Run Database Migrations

```bash
# Initialize Alembic (if not done)
alembic upgrade head
```

---

## 4. Dify AI Integration

### What is Dify?

**Dify** is a low-code AI workflow platform that allows you to create AI agents without coding. In this system, Dify is used **only for text generation**:

- ✅ Daily Executive Summaries
- ✅ Alert Explanations
- ✅ Board Email Drafts

**Important**: Dify does **NOT** handle risk calculations, limits, or data interpretation.

---

### Step 1: Install Dify (Self-Hosted)

**Using Docker Compose:**

```bash
# Create Dify directory
mkdir -p ~/dify
cd ~/dify

# Download Dify docker-compose
git clone https://github.com/langgenius/dify.git
cd dify/docker

# Start Dify
docker-compose up -d
```

**Wait 2-3 minutes for services to start, then access:**
- **Dify UI**: http://localhost:3001
- **API**: http://localhost:3001/v1

---

### Step 2: Create Dify Account

1. Open http://localhost:3001
2. Click "Sign Up"
3. Enter email/password
4. Verify email (if using real SMTP) or skip in dev mode

---

### Step 3: Configure AI Models in Dify

1. **Go to Settings** (top-right corner)
2. **Click "Model Provider"**
3. **Add OpenAI API Key** (or other provider):
   - Provider: OpenAI
   - API Key: `sk-...` (your OpenAI key)
   - Model: `gpt-4` or `gpt-3.5-turbo`
4. **Save**

**Alternative providers:**
- Azure OpenAI
- Anthropic Claude
- Cohere
- Local models (Ollama, LM Studio)

---

### Step 4: Create AI Workflows in Dify

#### Workflow 1: Daily Executive Summary

1. **Click "Create Workflow"** → "Text Generation"
2. **Name**: `Risk Executive Summary`
3. **Add Input Variables**:
   - `snapshot_date` (text)
   - `var_1d_95` (number)
   - `stressed_var` (number)
   - `dv01_total` (number)
   - `capital_ratio` (number)
   - `lcr_ratio` (number)
   - `critical_alerts` (text)
4. **Add LLM Node**:
   - Model: GPT-4
   - System Prompt:
     ```
     You are a risk management expert for an investment firm regulated by CySEC.
     Generate a concise executive summary (max 300 words) for the board of directors.
     
     Focus on:
     - Key risk metrics changes
     - Critical alerts and their business impact
     - Regulatory compliance status
     - Actionable recommendations
     
     Use professional, non-technical language.
     ```
   - User Prompt:
     ```
     Date: {{snapshot_date}}
     
     Market Risk:
     - VaR (1d 95%): {{var_1d_95}}
     - Stressed VaR: {{stressed_var}}
     - DV01: {{dv01_total}}
     
     Capital & Liquidity:
     - Capital Ratio: {{capital_ratio}}%
     - LCR: {{lcr_ratio}}%
     
     Critical Alerts:
     {{critical_alerts}}
     
     Generate executive summary.
     ```
5. **Publish Workflow**
6. **Get API Key**: Settings → API Keys → Create → Copy

---

#### Workflow 2: Alert Explanation

1. **Create New Workflow**: `Alert Explanation`
2. **Input Variables**:
   - `alert_type` (text)
   - `metric_name` (text)
   - `current_value` (number)
   - `limit_value` (number)
   - `severity` (text)
3. **LLM Node**:
   - System Prompt:
     ```
     You are a risk analyst. Explain alerts in simple terms for risk officers.
     Include:
     1. What happened
     2. Why it matters
     3. What actions to take
     ```
   - User Prompt:
     ```
     Alert Type: {{alert_type}}
     Metric: {{metric_name}}
     Current Value: {{current_value}}
     Limit: {{limit_value}}
     Severity: {{severity}}
     
     Explain this alert and recommend actions.
     ```
4. **Publish** → **Copy API Key**

---

### Step 5: Configure Dify in Risk Orchestrator

**Edit `.env`:**

```bash
# Dify Configuration
DIFY_API_URL=http://localhost:3001/v1
DIFY_API_KEY_SUMMARY=app-xxx...  # From Workflow 1
DIFY_API_KEY_ALERT=app-yyy...    # From Workflow 2
```

**Create Dify Service** (already implemented in code):

File: `app/services/dify_service.py`

```python
import httpx
from app.core.config import settings

async def generate_executive_summary(snapshot_data: dict) -> str:
    """Call Dify to generate executive summary"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.DIFY_API_URL}/workflows/run",
            headers={
                "Authorization": f"Bearer {settings.DIFY_API_KEY_SUMMARY}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": {
                    "snapshot_date": snapshot_data["snapshot_date"],
                    "var_1d_95": snapshot_data["var_1d_95"],
                    "stressed_var": snapshot_data["stressed_var"],
                    "dv01_total": snapshot_data["dv01_total"],
                    "capital_ratio": snapshot_data["capital_ratio"],
                    "lcr_ratio": snapshot_data["lcr_ratio"],
                    "critical_alerts": snapshot_data["critical_alerts"],
                },
                "response_mode": "blocking",
            },
        )
        result = response.json()
        return result["data"]["outputs"]["text"]

async def generate_alert_explanation(alert_data: dict) -> str:
    """Call Dify to explain alert"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.DIFY_API_URL}/workflows/run",
            headers={
                "Authorization": f"Bearer {settings.DIFY_API_KEY_ALERT}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": alert_data,
                "response_mode": "blocking",
            },
        )
        result = response.json()
        return result["data"]["outputs"]["text"]
```

---

## 5. Running the Application

### Start Backend (API)

```bash
# Activate virtual environment
source venv/bin/activate

# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API will be available at**: http://localhost:8000

**Swagger Docs**: http://localhost:8000/docs

---

### Start Frontend (React)

```bash
# In a new terminal
cd risk-frontend

# Start dev server
npm run dev
```

**Frontend will be available at**: http://localhost:3000

---

### Start Full Stack with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f risk-api

# Stop all services
docker-compose down
```

**Services:**
- API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

---

## 6. User Guide

### 6.1 First Login

**Default Admin Account** (create manually in DB):

```sql
INSERT INTO users (username, email, hashed_password, role, is_active)
VALUES (
  'admin',
  'admin@yourcompany.com',
  '$2b$12$...', -- Use bcrypt to hash password
  'ADMIN',
  true
);
```

**Generate Password Hash:**

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("your_password"))
```

**Login:**
1. Open http://localhost:3000
2. Username: `admin`
3. Password: `your_password`

---

### 6.2 Creating Portfolios

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "Cyprus Main Fund",
    "entity_id": 1,
    "base_currency": "EUR",
    "is_active": true
  }'
```

**Via Web UI:**
1. Dashboard → "Portfolios"
2. Click "Create Portfolio"
3. Fill in details
4. Save

---

### 6.3 Uploading Positions

**CSV Format** (`positions.csv`):

```csv
portfolio_name,instrument_type,isin,notional,clean_price,coupon_rate,maturity_date
Cyprus Main Fund,BOND,US912828Z230,1000000,98.5,0.025,2030-12-31
Cyprus Main Fund,BOND,DE0001102408,500000,102.0,0.035,2028-06-30
```

**Upload via API:**

```bash
curl -X POST http://localhost:8000/api/v1/batch/upload-positions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@positions.csv"
```

---

### 6.4 Running Risk Calculations

**On-Demand Calculation:**

```bash
curl -X POST http://localhost:8000/api/v1/risk/calculate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "as_of_date": "2024-12-01",
    "calculation_type": "FULL"
  }'
```

**Scheduled Nightly Batch:**
- Runs automatically at **00:00 UTC**
- Configured in `app/scheduler/jobs.py`

---

### 6.5 Viewing Risk Dashboard

1. **Open Dashboard**: http://localhost:3000
2. **Select Portfolio**: Dropdown at top
3. **View Metrics**:
   - VaR (1d 95%)
   - DV01
   - Capital Ratio
   - LCR
   - Active Alerts
4. **Check Charts**:
   - VaR Time Series (30 days)
   - Capital Adequacy Breakdown
5. **Review Alerts Table**:
   - Filter by severity
   - Acknowledge alerts

---

### 6.6 Generating PDF Reports

**Manual Generation:**

```bash
curl -X POST http://localhost:8000/api/v1/reports/pdf/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"report_date": "2024-12-01"}'
```

**Automatic Daily Reports:**
- Generated at **01:00 UTC** daily
- Saved to `/var/risk-reports/`
- Includes:
  - Executive Summary (from Dify)
  - VaR Charts
  - Critical Alerts
  - Top 5 News Events

---

### 6.7 Setting Risk Limits

**Create Limit:**

```bash
curl -X POST http://localhost:8000/api/v1/limits \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "limit_type": "VAR_1D_95",
    "limit_value": 100000,
    "warning_threshold": 0.8,
    "critical_threshold": 0.95,
    "is_active": true
  }'
```

**Limit Types:**
- `VAR_1D_95` - Value at Risk (1-day, 95%)
- `STRESSED_VAR` - Stressed VaR
- `DV01` - Interest rate sensitivity
- `CAPITAL_RATIO` - Regulatory capital ratio
- `LCR` - Liquidity Coverage Ratio

---

### 6.8 Managing Alerts

**View Active Alerts:**

```bash
curl http://localhost:8000/api/v1/alerts?acknowledged=false \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Acknowledge Alert:**

```bash
curl -X POST http://localhost:8000/api/v1/alerts/123/acknowledge \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Alert Severity Levels:**
- 🟢 **GREEN**: All good
- 🟡 **YELLOW**: Warning (80% of limit)
- 🔴 **RED**: Critical (95% of limit)
- 🔴 **CRITICAL**: Breach (>100% of limit)

---

## 7. API Documentation

### Authentication

**Get JWT Token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Use Token in Requests:**

```bash
curl http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### Key Endpoints

**Health Check:**
```
GET /api/v1/health
```

**Portfolios:**
```
GET    /api/v1/portfolios           # List all
POST   /api/v1/portfolios           # Create
GET    /api/v1/portfolios/{id}      # Get one
PUT    /api/v1/portfolios/{id}      # Update
DELETE /api/v1/portfolios/{id}      # Delete
```

**Risk Calculations:**
```
POST   /api/v1/risk/calculate       # On-demand calculation
GET    /api/v1/risk_snapshots       # List snapshots
GET    /api/v1/risk_snapshots/{id}  # Get snapshot details
```

**Alerts:**
```
GET    /api/v1/alerts               # List alerts
POST   /api/v1/alerts/{id}/acknowledge
```

**Reports:**
```
POST   /api/v1/reports/pdf/generate
GET    /api/v1/reports/pdf/download?report_date=2024-12-01
```

**Monitoring:**
```
GET    /api/v1/metrics              # Prometheus metrics
GET    /api/v1/audit                # Audit trail (admin only)
```

**Full API Documentation:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 8. Troubleshooting

### Issue: Database Connection Error

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
1. Check PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   # or
   pg_isready -h localhost -p 5432
   ```
2. Verify `DATABASE_URL` in `.env`
3. Check firewall settings

---

### Issue: Dify API Returns 401 Unauthorized

**Error:**
```
{"detail": "Invalid API key"}
```

**Solution:**
1. Verify API key in `.env` matches Dify workflow
2. Check Dify is running: http://localhost:3001
3. Regenerate API key in Dify if needed

---

### Issue: Frontend Can't Connect to Backend

**Error:**
```
Network Error: Failed to fetch
```

**Solution:**
1. Check backend is running on port 8000
2. Verify CORS settings in `.env`:
   ```bash
   CORS_ORIGINS=http://localhost:3000
   ```
3. Check `vite.config.ts` proxy settings

---

### Issue: Tests Failing

**Error:**
```
ERROR: could not connect to database
```

**Solution:**
1. Create test database:
   ```bash
   createdb risk_orchestrator_test
   ```
2. Run tests with correct env:
   ```bash
   export DATABASE_URL=postgresql+asyncpg://riskuser:password@localhost:5432/risk_orchestrator_test
   pytest
   ```

---

### Issue: Docker Compose Fails to Start

**Error:**
```
Error: port 5432 already in use
```

**Solution:**
1. Stop local PostgreSQL:
   ```bash
   brew services stop postgresql@15
   # or
   sudo systemctl stop postgresql
   ```
2. Or change port in `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Use 5433 on host
   ```

---

## Support & Documentation

- **GitHub Issues**: Report bugs and request features
- **API Docs**: http://localhost:8000/docs
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3001

---

## Security Best Practices

1. **Change default passwords** in production
2. **Use strong SECRET_KEY** (256-bit random)
3. **Enable HTTPS** with Let's Encrypt
4. **Restrict database access** to localhost or VPN
5. **Use Vault** for secrets management in production
6. **Enable rate limiting** on API endpoints
7. **Review audit logs** regularly
8. **Keep dependencies updated** (`pip install --upgrade`)

---

## Next Steps

1. ✅ Install and configure Dify
2. ✅ Run database migrations
3. ✅ Create admin user
4. ✅ Upload test positions
5. ✅ Run first risk calculation
6. ✅ Generate PDF report
7. ✅ Review alerts and set limits
8. ✅ Configure email/SMS notifications

**System is production-ready!** 🚀
