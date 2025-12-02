"""
Configuration management using Pydantic Settings
Loads from environment variables with validation
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Risk Orchestrator"
    APP_VERSION: str = "2.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development, staging, production
    
    # Security
    SECRET_KEY: str  # REQUIRED - JWT secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str  # REQUIRED - async postgresql URL
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    CACHE_TTL_SECONDS: int = 300
    
    # External APIs
    BLOOMBERG_API_KEY: Optional[str] = None
    REFINITIV_API_KEY: Optional[str] = None
    
    # Dify AI Integration
    DIFY_API_URL: Optional[str] = "http://localhost:3001/v1"
    DIFY_API_KEY_SUMMARY: Optional[str] = None  # For executive summary workflow
    DIFY_API_KEY_ALERT: Optional[str] = None    # For alert explanation workflow
    DIFY_API_KEY_EMAIL: Optional[str] = None    # For board email workflow
    
    # Email/SMS (for alerts)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMS_API_KEY: Optional[str] = None
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # Report storage
    REPORTS_DIR: str = "/var/risk-reports"
    S3_BUCKET: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
