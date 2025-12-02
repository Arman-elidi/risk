"""
Alert Engine - генерация алертов на основе лимитов и аномалий
Проверяет превышения лимитов, rating changes, margin calls, news events
"""
from datetime import datetime, date, timedelta
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.db.models import (
    Alert,
    Limit,
    RiskSnapshot,
    NewsEvent,
    Portfolio,
)

logger = structlog.get_logger()


def calculate_utilization(current_value: float, limit_value: float) -> float:
    """Calculate limit utilization as percentage"""
    if limit_value == 0:
        return 0.0
    return (current_value / limit_value) * 100.0


def determine_severity(
    utilization: float,
    warning_threshold: float,
    critical_threshold: float,
) -> str:
    """
    Determine alert severity based on utilization
    
    Returns: GREEN, YELLOW, RED, CRITICAL
    """
    if utilization >= critical_threshold:
        return 'CRITICAL'
    elif utilization >= warning_threshold:
        return 'RED'
    elif utilization >= warning_threshold * 0.8:
        return 'YELLOW'
    else:
        return 'GREEN'


async def check_limit_breaches(
    session: AsyncSession,
    snapshot: RiskSnapshot,
) -> List[Alert]:
    """
    Check for limit breaches in risk snapshot
    
    Compares snapshot metrics against configured limits
    """
    alerts = []
    
    # Load limits for portfolio
    result = await session.execute(
        select(Limit).where(
            Limit.portfolio_id == snapshot.portfolio_id,
            Limit.active == True,
        )
    )
    limits = result.scalars().all()
    
    logger.info("checking_limits", portfolio_id=snapshot.portfolio_id, limits_count=len(limits))
    
    for limit in limits:
        current_value = None
        
        # Map metric name to snapshot field
        if limit.metric_name == 'DV01':
            current_value = snapshot.dv01_total
        elif limit.metric_name == 'VAR_1D_95':
            current_value = snapshot.var_1d_95
        elif limit.metric_name == 'STRESSED_VAR':
            current_value = snapshot.stressed_var
        elif limit.metric_name == 'LCR':
            current_value = snapshot.lcr_ratio
        elif limit.metric_name == 'CAPITAL_RATIO':
            current_value = snapshot.capital_ratio
        elif limit.metric_name == 'CREDIT_VAR':
            current_value = snapshot.credit_var
        elif limit.metric_name == 'PFE_TOTAL':
            current_value = snapshot.pfe_current
        elif limit.metric_name == 'LIQUIDATION_COST_1D':
            current_value = snapshot.liquidation_cost_1d
        
        if current_value is None:
            continue
        
        # Calculate utilization
        utilization = calculate_utilization(current_value, limit.limit_value)
        severity = determine_severity(utilization, limit.warning_threshold, limit.critical_threshold)
        
        # Only create alert if threshold exceeded
        if severity in ('YELLOW', 'RED', 'CRITICAL'):
            alert = Alert(
                portfolio_id=snapshot.portfolio_id,
                risk_snapshot_id=snapshot.id,
                alert_type='LIMIT_BREACH',
                severity=severity,
                metric_name=limit.metric_name,
                current_value=current_value,
                threshold_value=limit.limit_value,
                description=f"{limit.metric_name} breach: {current_value:.2f} / {limit.limit_value:.2f} ({utilization:.1f}%)",
                recommendation=f"Review {limit.metric_name} exposure. Consider reducing positions." if severity == 'CRITICAL' else f"Monitor {limit.metric_name}.",
                created_at=datetime.utcnow(),
            )
            alerts.append(alert)
            
            logger.warning(
                "limit_breach_detected",
                metric=limit.metric_name,
                current=current_value,
                limit=limit.limit_value,
                severity=severity,
            )
    
    return alerts


async def check_anomalies(
    session: AsyncSession,
    snapshot: RiskSnapshot,
) -> List[Alert]:
    """
    Check for anomalies in risk metrics
    
    Compares current snapshot with recent history to detect unusual changes
    """
    alerts = []
    
    # Get recent snapshots (last 30 days)
    lookback_date = snapshot.snapshot_date - timedelta(days=30)
    result = await session.execute(
        select(RiskSnapshot).where(
            RiskSnapshot.portfolio_id == snapshot.portfolio_id,
            RiskSnapshot.snapshot_date >= lookback_date,
            RiskSnapshot.snapshot_date < snapshot.snapshot_date,
            RiskSnapshot.calculation_status == 'COMPLETED',
        ).order_by(RiskSnapshot.snapshot_date.desc()).limit(20)
    )
    recent_snapshots = result.scalars().all()
    
    if len(recent_snapshots) < 5:
        logger.info("insufficient_history_for_anomaly_detection", count=len(recent_snapshots))
        return alerts
    
    # Check VaR jump
    if snapshot.var_1d_95:
        avg_var = sum(s.var_1d_95 for s in recent_snapshots if s.var_1d_95) / len(recent_snapshots)
        var_change_pct = ((snapshot.var_1d_95 - avg_var) / avg_var) * 100.0 if avg_var > 0 else 0
        
        if abs(var_change_pct) > 30:  # 30% jump
            alert = Alert(
                portfolio_id=snapshot.portfolio_id,
                risk_snapshot_id=snapshot.id,
                alert_type='ANOMALY',
                severity='RED' if abs(var_change_pct) > 50 else 'YELLOW',
                metric_name='VAR_1D_95',
                current_value=snapshot.var_1d_95,
                threshold_value=avg_var,
                description=f"VaR jumped {var_change_pct:+.1f}% from 30-day average ({avg_var:.2f} → {snapshot.var_1d_95:.2f})",
                recommendation="Investigate sudden VaR increase. Check for new positions or market volatility.",
                created_at=datetime.utcnow(),
            )
            alerts.append(alert)
            logger.warning("var_anomaly_detected", change_pct=var_change_pct)
    
    # Check capital ratio drop
    if snapshot.capital_ratio:
        avg_ratio = sum(s.capital_ratio for s in recent_snapshots if s.capital_ratio) / len(recent_snapshots)
        ratio_change_pct = ((snapshot.capital_ratio - avg_ratio) / avg_ratio) * 100.0 if avg_ratio > 0 else 0
        
        if ratio_change_pct < -20:  # 20% drop
            alert = Alert(
                portfolio_id=snapshot.portfolio_id,
                risk_snapshot_id=snapshot.id,
                alert_type='ANOMALY',
                severity='CRITICAL',
                metric_name='CAPITAL_RATIO',
                current_value=snapshot.capital_ratio,
                threshold_value=avg_ratio,
                description=f"Capital ratio dropped {ratio_change_pct:.1f}% ({avg_ratio:.2f} → {snapshot.capital_ratio:.2f})",
                recommendation="Urgent: Review capital adequacy. Consider reducing risk-weighted assets.",
                created_at=datetime.utcnow(),
            )
            alerts.append(alert)
            logger.error("capital_ratio_drop_detected", change_pct=ratio_change_pct)
    
    return alerts


async def check_news_events(
    session: AsyncSession,
    snapshot: RiskSnapshot,
) -> List[Alert]:
    """
    Check for relevant news events affecting portfolio
    
    Looks for recent negative news on issuers/counterparties
    """
    alerts = []
    
    # Get recent negative news (last 7 days)
    lookback_date = snapshot.snapshot_date - timedelta(days=7)
    result = await session.execute(
        select(NewsEvent).where(
            NewsEvent.event_date >= lookback_date,
            NewsEvent.severity == 'NEGATIVE',
            NewsEvent.importance >= 3,
        )
    )
    news_events = result.scalars().all()
    
    for news in news_events:
        alert = Alert(
            portfolio_id=snapshot.portfolio_id,
            risk_snapshot_id=snapshot.id,
            issuer_id=news.issuer_id,
            alert_type='NEWS_EVENT',
            severity='YELLOW' if news.importance == 3 else 'RED',
            description=f"Negative news: {news.headline}",
            recommendation=f"Review exposure to {news.issuer_id}. Consider hedging or reducing position.",
            created_at=datetime.utcnow(),
        )
        alerts.append(alert)
    
    logger.info("news_events_checked", count=len(news_events))
    return alerts


async def generate_alerts(
    session: AsyncSession,
    snapshot: RiskSnapshot,
) -> List[Alert]:
    """
    Main alert generation function
    
    Checks:
    - Limit breaches
    - Anomalies (unusual changes)
    - News events
    - Margin calls (TODO)
    - Rating changes (TODO)
    
    Returns list of Alert objects (not yet saved to DB)
    """
    logger.info("generate_alerts_started", snapshot_id=snapshot.id, portfolio_id=snapshot.portfolio_id)
    
    all_alerts = []
    
    # 1. Check limit breaches
    limit_alerts = await check_limit_breaches(session, snapshot)
    all_alerts.extend(limit_alerts)
    
    # 2. Check anomalies
    anomaly_alerts = await check_anomalies(session, snapshot)
    all_alerts.extend(anomaly_alerts)
    
    # 3. Check news events
    news_alerts = await check_news_events(session, snapshot)
    all_alerts.extend(news_alerts)
    
    # 4. TODO: Check margin calls (CCR-based)
    # 5. TODO: Check rating changes
    
    logger.info(
        "generate_alerts_completed",
        total_alerts=len(all_alerts),
        by_severity={
            'CRITICAL': sum(1 for a in all_alerts if a.severity == 'CRITICAL'),
            'RED': sum(1 for a in all_alerts if a.severity == 'RED'),
            'YELLOW': sum(1 for a in all_alerts if a.severity == 'YELLOW'),
        }
    )
    
    return all_alerts


async def save_alerts(session: AsyncSession, alerts: List[Alert]) -> int:
    """Save alerts to database"""
    for alert in alerts:
        session.add(alert)
    
    await session.commit()
    logger.info("alerts_saved", count=len(alerts))
    return len(alerts)
