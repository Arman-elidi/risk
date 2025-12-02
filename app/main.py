from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.api.risk import router as risk_router
from app.api.batch import router as batch_router
from app.api.portfolios import router as portfolios_router
from app.api.alerts import router as alerts_router
from app.api.limits import router as limits_router
from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.monitoring import router as monitoring_router
from app.api.dify import router as dify_router
from app.api.stress import router as stress_router
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.middleware.monitoring_middleware import MonitoringMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.core.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start scheduler
    logger.info("application_startup", version="2.1.0", environment=settings.ENVIRONMENT)
    start_scheduler()
    yield
    # Shutdown: Stop scheduler
    logger.info("application_shutdown")
    stop_scheduler()


app = FastAPI(
    title="AI Risk Orchestrator API",
    version="2.1",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware (Prometheus metrics)
app.add_middleware(MonitoringMiddleware)

# Add rate limiting middleware (per techspec 3.1)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Base path prefix
BASE_PREFIX = "/api/v1"

# Include routers under /api/v1
app.include_router(monitoring_router, prefix=BASE_PREFIX, tags=["monitoring"])
app.include_router(health_router, prefix=BASE_PREFIX)
app.include_router(portfolios_router, prefix=BASE_PREFIX, tags=["portfolios"])
app.include_router(risk_router, prefix=BASE_PREFIX, tags=["risk"])
app.include_router(batch_router, prefix=BASE_PREFIX, tags=["batch"])
app.include_router(alerts_router, prefix=BASE_PREFIX, tags=["alerts"])
app.include_router(limits_router, prefix=BASE_PREFIX, tags=["limits"])
app.include_router(reports_router, prefix=BASE_PREFIX, tags=["reports"])
app.include_router(dify_router, prefix=BASE_PREFIX, tags=["dify-ai"])
app.include_router(stress_router, prefix=BASE_PREFIX, tags=["stress-testing"])
