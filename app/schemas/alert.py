from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Alert(BaseModel):
    id: int
    portfolio_id: Optional[int] = None
    risk_snapshot_id: Optional[str] = None
    issuer_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    alert_type: str  # LIMIT_BREACH, ANOMALY, RATING_CHANGE, MARGIN_CALL, NEWS_EVENT
    severity: str  # GREEN/YELLOW/RED/CRITICAL
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    description: str
    recommendation: Optional[str] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

class AlertAcknowledge(BaseModel):
    comment: Optional[str] = None

class AlertEscalate(BaseModel):
    level: str
    comment: Optional[str] = None
