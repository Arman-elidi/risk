"""
Monitoring and health endpoints
Prometheus metrics, health checks, audit logs
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.monitoring import metrics_endpoint
from app.core.audit import get_audit_trail
from app.db.session import get_db
from app.core.auth import require_admin

router = APIRouter()


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format
    """
    return await metrics_endpoint()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "risk-orchestrator",
        "version": "2.1.0",
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check for Kubernetes
    
    Checks:
    - Database connectivity
    - Critical services
    """
    try:
        # Check database
        await db.execute("SELECT 1")
        
        return {
            "ready": True,
            "checks": {
                "database": "ok",
            }
        }
    except Exception as e:
        return {
            "ready": False,
            "checks": {
                "database": f"error: {str(e)}",
            }
        }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes
    
    Simple check that service is running
    """
    return {"alive": True}


@router.get("/audit")
async def get_audit_logs(
    entity_type: str = None,
    entity_id: int = None,
    user_id: int = None,
    event_type: str = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """
    Retrieve audit trail
    
    Args:
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        user_id: Filter by user
        event_type: Filter by event type
        limit: Max records (default 100)
    
    Returns:
        List of audit log entries
    """
    logs = await get_audit_trail(
        session=db,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        event_type=event_type,
        limit=limit,
    )
    
    return {
        "count": len(logs),
        "logs": [
            {
                "log_id": log.log_id,
                "event_type": log.event_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "user_id": log.user_id,
                "action": log.action,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "metadata": log.metadata,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
