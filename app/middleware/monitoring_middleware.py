"""
Middleware for Prometheus metrics and request tracking
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog

from app.core.monitoring import (
    http_requests_total,
    http_request_duration_seconds,
)

logger = structlog.get_logger()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Track HTTP requests with Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error("request_failed", path=request.url.path, error=str(e))
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            # Normalize endpoint path (remove IDs)
            endpoint = request.url.path
            for segment in endpoint.split('/'):
                if segment.isdigit():
                    endpoint = endpoint.replace(segment, '{id}')
            
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=status_code,
                duration_ms=round(duration * 1000, 2),
            )
        
        return response
