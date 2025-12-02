"""
Rate Limiting Middleware
Per techspec section 3.1 (API Gateway requirements)
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from typing import Dict
import structlog

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting
    
    Per techspec 3.1: rate limiting on API Gateway
    
    Production: use Redis with sliding window or token bucket
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        
        # In-memory storage: client_id -> [(timestamp, count)]
        self.requests: Dict[str, list] = defaultdict(list)
    
    def get_client_id(self, request: Request) -> str:
        """Extract client identifier"""
        # Priority: user from JWT > IP address
        user_id = None
        
        # Try to extract from JWT (if authenticated)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, decode JWT to get user_id
            # For now, use IP
            pass
        
        # Fallback to IP
        client_ip = request.client.host if request.client else "unknown"
        return user_id or f"ip:{client_ip}"
    
    def is_rate_limited(self, client_id: str) -> bool:
        """Check if client exceeded rate limit"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_id] = [
            ts for ts in self.requests[client_id]
            if ts > window_start
        ]
        
        # Check limit
        current_count = len(self.requests[client_id])
        
        if current_count >= self.requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                count=current_count,
                limit=self.requests_per_minute,
            )
            return True
        
        # Add current request
        self.requests[client_id].append(now)
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health checks
        if request.url.path in ["/api/v1/health", "/api/v1/health/live", "/api/v1/health/ready"]:
            return await call_next(request)
        
        client_id = self.get_client_id(request)
        
        if self.is_rate_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail={
                    "status": 429,
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.requests[client_id]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))
        
        return response
