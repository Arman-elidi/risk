"""
Dify AI Integration Service
Generates text using Dify workflows for executive summaries and alert explanations
"""
import httpx
import structlog
from typing import Dict, Any, Optional
from app.core.config import settings

logger = structlog.get_logger()


async def generate_executive_summary(snapshot_data: Dict[str, Any]) -> str:
    """
    Generate executive summary using Dify AI workflow
    
    Args:
        snapshot_data: Risk snapshot data containing:
            - snapshot_date: Date of snapshot
            - var_1d_95: Value at Risk (1-day, 95%)
            - stressed_var: Stressed VaR
            - dv01_total: Total DV01
            - capital_ratio: Capital adequacy ratio
            - lcr_ratio: Liquidity coverage ratio
            - critical_alerts: Summary of critical alerts
    
    Returns:
        Generated executive summary text (max 300 words)
    """
    if not hasattr(settings, 'DIFY_API_KEY_SUMMARY'):
        logger.warning("dify_summary_disabled", reason="DIFY_API_KEY_SUMMARY not configured")
        return "[Executive summary generation disabled - Dify not configured]"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {settings.DIFY_API_KEY_SUMMARY}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": {
                        "snapshot_date": str(snapshot_data.get("snapshot_date", "")),
                        "var_1d_95": float(snapshot_data.get("var_1d_95", 0)),
                        "stressed_var": float(snapshot_data.get("stressed_var", 0)),
                        "dv01_total": float(snapshot_data.get("dv01_total", 0)),
                        "capital_ratio": float(snapshot_data.get("capital_ratio", 0)),
                        "lcr_ratio": float(snapshot_data.get("lcr_ratio", 0)),
                        "critical_alerts": str(snapshot_data.get("critical_alerts", "None")),
                    },
                    "response_mode": "blocking",
                    "user": "risk-system",
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract text from Dify response
            summary = result.get("data", {}).get("outputs", {}).get("text", "")
            
            if not summary:
                logger.warning("dify_summary_empty", response=result)
                return "[Empty summary generated]"
            
            logger.info(
                "executive_summary_generated",
                length=len(summary),
                snapshot_date=snapshot_data.get("snapshot_date"),
            )
            return summary
            
    except httpx.HTTPStatusError as e:
        logger.error(
            "dify_summary_http_error",
            status_code=e.response.status_code,
            error=str(e),
        )
        return f"[Error generating summary: HTTP {e.response.status_code}]"
    
    except httpx.RequestError as e:
        logger.error("dify_summary_request_error", error=str(e))
        return f"[Error connecting to Dify: {str(e)}]"
    
    except Exception as e:
        logger.error("dify_summary_failed", error=str(e), error_type=type(e).__name__)
        return f"[Unexpected error generating summary: {str(e)}]"


async def generate_alert_explanation(alert_data: Dict[str, Any]) -> str:
    """
    Generate alert explanation using Dify AI workflow
    
    Args:
        alert_data: Alert data containing:
            - alert_type: Type of alert (LIMIT_BREACH, ANOMALY, NEWS_EVENT)
            - metric_name: Metric that triggered alert
            - current_value: Current value of metric
            - limit_value: Limit value (if applicable)
            - severity: Alert severity (GREEN, YELLOW, RED, CRITICAL)
            - description: Brief description of alert
    
    Returns:
        Generated explanation text with recommended actions
    """
    if not hasattr(settings, 'DIFY_API_KEY_ALERT'):
        logger.warning("dify_alert_disabled", reason="DIFY_API_KEY_ALERT not configured")
        return "[Alert explanation disabled - Dify not configured]"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {settings.DIFY_API_KEY_ALERT}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": {
                        "alert_type": str(alert_data.get("alert_type", "")),
                        "metric_name": str(alert_data.get("metric_name", "")),
                        "current_value": float(alert_data.get("current_value", 0)),
                        "limit_value": float(alert_data.get("limit_value", 0)),
                        "severity": str(alert_data.get("severity", "")),
                        "description": str(alert_data.get("description", "")),
                    },
                    "response_mode": "blocking",
                    "user": "risk-system",
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract text from Dify response
            explanation = result.get("data", {}).get("outputs", {}).get("text", "")
            
            if not explanation:
                logger.warning("dify_explanation_empty", response=result)
                return "[Empty explanation generated]"
            
            logger.info(
                "alert_explanation_generated",
                alert_type=alert_data.get("alert_type"),
                severity=alert_data.get("severity"),
            )
            return explanation
            
    except httpx.HTTPStatusError as e:
        logger.error(
            "dify_alert_http_error",
            status_code=e.response.status_code,
            error=str(e),
        )
        return f"[Error generating explanation: HTTP {e.response.status_code}]"
    
    except httpx.RequestError as e:
        logger.error("dify_alert_request_error", error=str(e))
        return f"[Error connecting to Dify: {str(e)}]"
    
    except Exception as e:
        logger.error("dify_alert_failed", error=str(e), error_type=type(e).__name__)
        return f"[Unexpected error generating explanation: {str(e)}]"


async def generate_board_email(email_data: Dict[str, Any]) -> str:
    """
    Generate board email draft using Dify AI workflow
    
    Args:
        email_data: Email context data containing:
            - subject: Email subject
            - period: Reporting period
            - key_points: List of key points to include
            - risk_summary: Summary of risk metrics
    
    Returns:
        Generated email draft
    """
    if not hasattr(settings, 'DIFY_API_KEY_EMAIL'):
        logger.warning("dify_email_disabled", reason="DIFY_API_KEY_EMAIL not configured")
        return "[Board email generation disabled - Dify not configured]"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {settings.DIFY_API_KEY_EMAIL}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": email_data,
                    "response_mode": "blocking",
                    "user": "risk-system",
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            email_draft = result.get("data", {}).get("outputs", {}).get("text", "")
            
            if not email_draft:
                logger.warning("dify_email_empty", response=result)
                return "[Empty email draft generated]"
            
            logger.info("board_email_generated", subject=email_data.get("subject"))
            return email_draft
            
    except Exception as e:
        logger.error("dify_email_failed", error=str(e))
        return f"[Error generating email: {str(e)}]"
