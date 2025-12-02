"""
Prometheus metrics for monitoring
Tracks API latency, calculation times, errors, alerts
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps
import time
import structlog

logger = structlog.get_logger()

# Application info
app_info = Info('risk_orchestrator', 'Risk Orchestrator application info')
app_info.info({
    'version': '2.1.0',
    'environment': 'production',
})

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Risk Calculation Metrics
risk_calculations_total = Counter(
    'risk_calculations_total',
    'Total risk calculations performed',
    ['portfolio_id', 'calculation_type', 'status']
)

risk_calculation_duration_seconds = Histogram(
    'risk_calculation_duration_seconds',
    'Risk calculation duration',
    ['portfolio_id', 'calculation_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0]
)

# Alert Metrics
alerts_generated_total = Counter(
    'alerts_generated_total',
    'Total alerts generated',
    ['severity', 'alert_type']
)

alerts_active = Gauge(
    'alerts_active',
    'Number of active (unacknowledged) alerts',
    ['severity']
)

# ETL Metrics
etl_jobs_total = Counter(
    'etl_jobs_total',
    'Total ETL jobs executed',
    ['job_name', 'status']
)

etl_job_duration_seconds = Histogram(
    'etl_job_duration_seconds',
    'ETL job duration',
    ['job_name'],
    buckets=[10, 30, 60, 120, 300, 600]
)

etl_rows_processed = Counter(
    'etl_rows_processed_total',
    'Total rows processed by ETL',
    ['job_name']
)

# Database Metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type']
)

db_connection_errors = Counter(
    'db_connection_errors_total',
    'Database connection errors'
)

# Report Metrics
pdf_reports_generated = Counter(
    'pdf_reports_generated_total',
    'Total PDF reports generated',
    ['status']
)

pdf_generation_duration_seconds = Histogram(
    'pdf_generation_duration_seconds',
    'PDF generation duration'
)

# Limit Breach Metrics
limit_breaches_total = Counter(
    'limit_breaches_total',
    'Total limit breaches detected',
    ['limit_type', 'severity']
)

limit_utilization = Gauge(
    'limit_utilization_percent',
    'Current limit utilization percentage',
    ['portfolio_id', 'limit_type']
)


def track_time(metric_histogram):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric_histogram.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric_histogram.observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
