from typing import Optional
from pydantic import BaseModel

class Limit(BaseModel):
    id: int
    portfolio_id: int
    limit_type: str  # DV01, VaR, K, LCR, CONCENTRATION, PFE, NEWS
    metric_name: str
    limit_value: float
    warning_threshold: float
    critical_threshold: float
    active: bool = True

class LimitCreate(BaseModel):
    portfolio_id: int
    limit_type: str
    metric_name: str
    limit_value: float
    warning_threshold: float
    critical_threshold: float
    active: bool = True

class LimitUpdate(BaseModel):
    limit_type: Optional[str] = None
    metric_name: Optional[str] = None
    limit_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    active: Optional[bool] = None

class LimitActivePatch(BaseModel):
    active: bool
