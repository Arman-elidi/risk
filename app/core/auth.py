from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Load configuration from environment
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class RoleChecker:
    """Dependency to check user roles (RBAC)"""
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(lambda: get_current_user)):
        if user.get("role") not in self.allowed_roles:
            logger.warning(
                "access_denied",
                user_id=user.get("user_id"),
                role=user.get("role"),
                required_roles=self.allowed_roles,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "status": 403,
                    "code": "FORBIDDEN",
                    "message": "Insufficient permissions",
                    "details": {"required_roles": self.allowed_roles},
                },
            )
        return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail={
                "status": 401,
                "code": "INVALID_TOKEN",
                "message": "Invalid authentication token",
            },
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail={"status": 401, "code": "INVALID_TOKEN", "message": "Invalid token payload"},
        )
    
    # Return user data from token
    # In production, fetch from database
    return {
        "user_id": user_id,
        "username": payload.get("username"),
        "role": payload.get("role", "VIEWER"),
        "scopes": payload.get("scopes", []),
    }


# Legacy auth_bearer for backwards compatibility
async def auth_bearer(user: dict = Depends(get_current_user)):
    """Legacy auth dependency - use get_current_user instead"""
    return user


# Role-based dependencies
require_admin = RoleChecker(["ADMIN"])
require_risk_or_admin = RoleChecker(["ADMIN", "RISK"])
require_trader_or_above = RoleChecker(["ADMIN", "RISK", "TRADER"])
