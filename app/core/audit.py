"""
Enhanced audit logging to database
Tracks all risk calculations, limit changes, user actions
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.db.models import AuditLog

logger = structlog.get_logger()


async def log_audit_event(
    session: AsyncSession,
    event_type: str,
    entity_type: str,
    entity_id: int,
    user_id: int,
    action: str,
    old_value: str = None,
    new_value: str = None,
    metadata: dict = None,
):
    """
    Create audit log entry
    
    Args:
        event_type: RISK_CALCULATION, LIMIT_CHANGE, USER_ACTION, DATA_CHANGE
        entity_type: Portfolio, Position, Limit, Alert, etc.
        entity_id: ID of the entity
        user_id: User who performed the action
        action: CREATE, UPDATE, DELETE, CALCULATE, ACKNOWLEDGE
        old_value: Previous value (for updates)
        new_value: New value (for updates)
        metadata: Additional context
    """
    try:
        audit = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        
        session.add(audit)
        await session.flush()
        
        logger.info(
            "audit_event",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
        )
        
    except Exception as e:
        logger.error("audit_log_failed", error=str(e), event_type=event_type)
        # Don't fail the main operation if audit logging fails
        pass


async def log_risk_calculation(
    session: AsyncSession,
    portfolio_id: int,
    user_id: int,
    calculation_type: str,
    status: str,
    duration_ms: float,
    snapshot_id: int = None,
    error_message: str = None,
):
    """Log risk calculation event"""
    await log_audit_event(
        session=session,
        event_type="RISK_CALCULATION",
        entity_type="Portfolio",
        entity_id=portfolio_id,
        user_id=user_id,
        action=calculation_type,  # NIGHTLY_BATCH, ON_DEMAND, STRESS_TEST
        new_value=status,  # SUCCESS, FAILED
        metadata={
            "snapshot_id": snapshot_id,
            "duration_ms": duration_ms,
            "error_message": error_message,
        },
    )


async def log_limit_change(
    session: AsyncSession,
    limit_id: int,
    user_id: int,
    old_limit: float,
    new_limit: float,
    reason: str = None,
):
    """Log limit change event"""
    await log_audit_event(
        session=session,
        event_type="LIMIT_CHANGE",
        entity_type="Limit",
        entity_id=limit_id,
        user_id=user_id,
        action="UPDATE",
        old_value=str(old_limit),
        new_value=str(new_limit),
        metadata={"reason": reason},
    )


async def log_user_action(
    session: AsyncSession,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    details: dict = None,
):
    """Log general user action"""
    await log_audit_event(
        session=session,
        event_type="USER_ACTION",
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        metadata=details,
    )


async def get_audit_trail(
    session: AsyncSession,
    entity_type: str = None,
    entity_id: int = None,
    user_id: int = None,
    event_type: str = None,
    limit: int = 100,
) -> list[AuditLog]:
    """
    Retrieve audit trail with filters
    
    Args:
        entity_type: Filter by entity type
        entity_id: Filter by specific entity
        user_id: Filter by user
        event_type: Filter by event type
        limit: Max records to return
    
    Returns:
        List of audit log entries
    """
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    
    query = query.limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())
