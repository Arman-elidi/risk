"""
Unit tests for audit logging
"""
import pytest
from datetime import datetime
from app.core.audit import (
    log_audit_event,
    log_risk_calculation,
    log_limit_change,
    get_audit_trail,
)
from app.db.models import AuditLog


@pytest.mark.integration
class TestAuditLogging:
    """Test audit logging functionality"""
    
    async def test_log_audit_event(self, db_session):
        """Test creating audit log entry"""
        await log_audit_event(
            session=db_session,
            event_type="USER_ACTION",
            entity_type="Portfolio",
            entity_id=1,
            user_id=100,
            action="CREATE",
            new_value="New Portfolio",
            metadata={"source": "API"},
        )
        
        await db_session.commit()
        
        # Verify log was created
        logs = await get_audit_trail(
            session=db_session,
            entity_type="Portfolio",
            entity_id=1,
        )
        
        assert len(logs) == 1
        assert logs[0].event_type == "USER_ACTION"
        assert logs[0].action == "CREATE"
        assert logs[0].user_id == 100
        assert logs[0].metadata["source"] == "API"
    
    async def test_log_risk_calculation(self, db_session):
        """Test logging risk calculation event"""
        await log_risk_calculation(
            session=db_session,
            portfolio_id=1,
            user_id=100,
            calculation_type="NIGHTLY_BATCH",
            status="SUCCESS",
            duration_ms=2500.0,
            snapshot_id=123,
        )
        
        await db_session.commit()
        
        logs = await get_audit_trail(
            session=db_session,
            event_type="RISK_CALCULATION",
        )
        
        assert len(logs) == 1
        assert logs[0].action == "NIGHTLY_BATCH"
        assert logs[0].new_value == "SUCCESS"
        assert logs[0].metadata["duration_ms"] == 2500.0
    
    async def test_log_limit_change(self, db_session):
        """Test logging limit change"""
        await log_limit_change(
            session=db_session,
            limit_id=10,
            user_id=100,
            old_limit=100000.0,
            new_limit=150000.0,
            reason="Risk appetite increased",
        )
        
        await db_session.commit()
        
        logs = await get_audit_trail(
            session=db_session,
            event_type="LIMIT_CHANGE",
        )
        
        assert len(logs) == 1
        assert logs[0].old_value == "100000.0"
        assert logs[0].new_value == "150000.0"
        assert logs[0].metadata["reason"] == "Risk appetite increased"
    
    async def test_get_audit_trail_filters(self, db_session):
        """Test audit trail retrieval with filters"""
        # Create multiple audit entries
        for i in range(5):
            await log_audit_event(
                session=db_session,
                event_type="USER_ACTION",
                entity_type="Portfolio",
                entity_id=i,
                user_id=100,
                action="UPDATE",
            )
        
        for i in range(3):
            await log_audit_event(
                session=db_session,
                event_type="RISK_CALCULATION",
                entity_type="Portfolio",
                entity_id=1,
                user_id=200,
                action="CALCULATE",
            )
        
        await db_session.commit()
        
        # Filter by user
        user_100_logs = await get_audit_trail(
            session=db_session,
            user_id=100,
        )
        assert len(user_100_logs) == 5
        
        # Filter by event type
        risk_logs = await get_audit_trail(
            session=db_session,
            event_type="RISK_CALCULATION",
        )
        assert len(risk_logs) == 3
        
        # Filter by entity
        entity_1_logs = await get_audit_trail(
            session=db_session,
            entity_id=1,
        )
        assert len(entity_1_logs) == 4  # 1 USER_ACTION + 3 RISK_CALCULATION
    
    async def test_audit_trail_ordering(self, db_session):
        """Test audit trail is ordered by time (newest first)"""
        import asyncio
        
        # Create entries with small delays
        for i in range(3):
            await log_audit_event(
                session=db_session,
                event_type="USER_ACTION",
                entity_type="Test",
                entity_id=i,
                user_id=100,
                action=f"ACTION_{i}",
            )
            await asyncio.sleep(0.01)  # Small delay
        
        await db_session.commit()
        
        logs = await get_audit_trail(session=db_session, limit=10)
        
        # Should be ordered newest first
        assert logs[0].action == "ACTION_2"
        assert logs[1].action == "ACTION_1"
        assert logs[2].action == "ACTION_0"
