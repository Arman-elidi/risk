"""
Dify AI Integration Endpoints
Test and use Dify AI text generation
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.core.auth import require_risk_or_admin
from app.services.dify_service import (
    generate_executive_summary,
    generate_alert_explanation,
    generate_board_email,
)

router = APIRouter()


class SummaryRequest(BaseModel):
    """Request for executive summary generation"""
    snapshot_date: date
    var_1d_95: float
    stressed_var: float
    dv01_total: float
    capital_ratio: float
    lcr_ratio: float
    critical_alerts: str


class AlertExplanationRequest(BaseModel):
    """Request for alert explanation"""
    alert_type: str
    metric_name: str
    current_value: float
    limit_value: Optional[float] = None
    severity: str
    description: Optional[str] = None


class EmailRequest(BaseModel):
    """Request for board email generation"""
    subject: str
    period: str
    key_points: str
    risk_summary: str


@router.post("/dify/summary")
async def generate_summary(
    request: SummaryRequest,
    user=Depends(require_risk_or_admin),
):
    """
    Generate executive summary using Dify AI
    
    **Required role**: RISK or ADMIN
    
    Returns:
        Generated summary text (max 300 words)
    """
    summary = await generate_executive_summary({
        "snapshot_date": request.snapshot_date,
        "var_1d_95": request.var_1d_95,
        "stressed_var": request.stressed_var,
        "dv01_total": request.dv01_total,
        "capital_ratio": request.capital_ratio,
        "lcr_ratio": request.lcr_ratio,
        "critical_alerts": request.critical_alerts,
    })
    
    return {
        "summary": summary,
        "snapshot_date": request.snapshot_date,
        "generated_by": "Dify AI",
    }


@router.post("/dify/alert-explanation")
async def explain_alert(
    request: AlertExplanationRequest,
    user=Depends(require_risk_or_admin),
):
    """
    Generate alert explanation using Dify AI
    
    **Required role**: RISK or ADMIN
    
    Returns:
        Explanation with recommended actions
    """
    explanation = await generate_alert_explanation({
        "alert_type": request.alert_type,
        "metric_name": request.metric_name,
        "current_value": request.current_value,
        "limit_value": request.limit_value or 0,
        "severity": request.severity,
        "description": request.description or "",
    })
    
    return {
        "explanation": explanation,
        "alert_type": request.alert_type,
        "severity": request.severity,
        "generated_by": "Dify AI",
    }


@router.post("/dify/board-email")
async def create_board_email(
    request: EmailRequest,
    user=Depends(require_risk_or_admin),
):
    """
    Generate board email draft using Dify AI
    
    **Required role**: RISK or ADMIN
    
    Returns:
        Email draft ready to send
    """
    email_draft = await generate_board_email({
        "subject": request.subject,
        "period": request.period,
        "key_points": request.key_points,
        "risk_summary": request.risk_summary,
    })
    
    return {
        "email_draft": email_draft,
        "subject": request.subject,
        "generated_by": "Dify AI",
    }


@router.get("/dify/health")
async def check_dify_health(user=Depends(require_risk_or_admin)):
    """
    Check Dify AI service health
    
    **Required role**: RISK or ADMIN
    
    Returns:
        Status of Dify integration
    """
    from app.core.config import settings
    
    return {
        "dify_url": settings.DIFY_API_URL,
        "summary_configured": hasattr(settings, 'DIFY_API_KEY_SUMMARY') and settings.DIFY_API_KEY_SUMMARY is not None,
        "alert_configured": hasattr(settings, 'DIFY_API_KEY_ALERT') and settings.DIFY_API_KEY_ALERT is not None,
        "email_configured": hasattr(settings, 'DIFY_API_KEY_EMAIL') and settings.DIFY_API_KEY_EMAIL is not None,
    }
