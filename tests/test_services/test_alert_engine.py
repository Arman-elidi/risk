"""
Unit tests for alert engine
"""
import pytest
from datetime import date, datetime
from app.db.models import RiskSnapshot, Limit
from app.services.alert_engine import (
    check_limit_breaches,
    determine_severity,
    check_anomalies,
)


@pytest.mark.integration
class TestAlertEngine:
    """Test alert generation logic"""
    
    async def test_check_limit_breaches(self, db_session):
        """Test limit breach detection"""
        # Create test limit
        limit = Limit(
            portfolio_id=1,
            limit_type="VAR_1D_95",
            limit_value=100000.0,
            warning_threshold=0.8,
            critical_threshold=0.95,
            is_active=True,
        )
        db_session.add(limit)
        await db_session.commit()
        
        # Create snapshot with breach
        snapshot = RiskSnapshot(
            portfolio_id=1,
            snapshot_date=date.today(),
            calculation_timestamp=datetime.utcnow(),
            calculation_status="SUCCESS",
            var_1d_95=-120000.0,  # Breaches limit
            stressed_var=-150000.0,
            dv01_total=5000.0,
        )
        db_session.add(snapshot)
        await db_session.commit()
        await db_session.refresh(snapshot)
        
        # Check for breaches
        alerts = await check_limit_breaches(db_session, snapshot)
        
        # Should generate alert for VAR breach
        var_alerts = [a for a in alerts if a.metric_name == "VAR_1D_95"]
        assert len(var_alerts) > 0
        assert var_alerts[0].alert_type == "LIMIT_BREACH"
        assert var_alerts[0].severity in ["RED", "CRITICAL"]
    
    def test_determine_severity(self):
        """Test severity determination logic"""
        # Below warning
        severity = determine_severity(0.5, 0.8, 0.95)
        assert severity == "GREEN"
        
        # Warning level
        severity = determine_severity(0.85, 0.8, 0.95)
        assert severity == "YELLOW"
        
        # Critical level
        severity = determine_severity(0.97, 0.8, 0.95)
        assert severity == "CRITICAL"
        
        # At warning threshold
        severity = determine_severity(0.8, 0.8, 0.95)
        assert severity in ["YELLOW", "RED"]
    
    async def test_check_anomalies(self, db_session):
        """Test anomaly detection"""
        # Create historical snapshots
        for i in range(30):
            snapshot = RiskSnapshot(
                portfolio_id=1,
                snapshot_date=date(2024, 1, i + 1),
                calculation_timestamp=datetime.utcnow(),
                calculation_status="SUCCESS",
                var_1d_95=-50000.0,  # Stable VaR
                stressed_var=-70000.0,
                dv01_total=3000.0,
            )
            db_session.add(snapshot)
        
        # Create current snapshot with anomaly
        current = RiskSnapshot(
            portfolio_id=1,
            snapshot_date=date(2024, 2, 1),
            calculation_timestamp=datetime.utcnow(),
            calculation_status="SUCCESS",
            var_1d_95=-100000.0,  # 2x increase (anomaly)
            stressed_var=-140000.0,
            dv01_total=3000.0,
        )
        db_session.add(current)
        await db_session.commit()
        await db_session.refresh(current)
        
        # Check for anomalies
        alerts = await check_anomalies(db_session, current)
        
        # Should detect VaR jump
        var_anomalies = [a for a in alerts if "VaR" in a.description]
        assert len(var_anomalies) > 0
        assert var_anomalies[0].alert_type == "ANOMALY"
