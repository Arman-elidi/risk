from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from app.core.auth import auth_bearer
from app.schemas.alert import Alert, AlertAcknowledge, AlertEscalate

router = APIRouter()

# In-memory placeholder
_ALERTS = {}
_NEXT_ALERT_ID = 1


@router.get("/alerts", response_model=List[Alert])
def list_alerts(
    portfolio_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    user=Depends(auth_bearer),
):
    results = list(_ALERTS.values())
    if portfolio_id is not None:
        results = [a for a in results if a.portfolio_id == portfolio_id]
    if alert_type:
        results = [a for a in results if a.alert_type == alert_type]
    if severity:
        results = [a for a in results if a.severity == severity]
    if acknowledged is not None:
        results = [a for a in results if a.acknowledged == acknowledged]
    return results


@router.post("/alerts/{alert_id}/ack", response_model=Alert)
def acknowledge_alert(alert_id: int, body: AlertAcknowledge, user=Depends(auth_bearer)):
    if alert_id not in _ALERTS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Alert not found"})
    alert = _ALERTS[alert_id]
    alert.acknowledged = True
    alert.acknowledged_by = user.get("user_id")
    alert.acknowledged_at = datetime.utcnow()
    return alert


@router.post("/alerts/{alert_id}/escalate", response_model=Alert)
def escalate_alert(alert_id: int, body: AlertEscalate, user=Depends(auth_bearer)):
    if alert_id not in _ALERTS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Alert not found"})
    alert = _ALERTS[alert_id]
    # Mock escalation logic
    alert.description += f"\n[Escalated to {body.level}]: {body.comment or ''}"
    return alert
