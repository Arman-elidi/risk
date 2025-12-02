"""
VaR Backtesting Service
Per techspec section 12
"""
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from app.db.models import VaRBacktesting, RiskSnapshot

logger = structlog.get_logger()


async def record_var_forecast(
    session: AsyncSession,
    portfolio_id: int,
    as_of_date: date,
    var_forecast: float,
) -> None:
    """
    Morning: record VaR forecast from yesterday's calculation
    Per techspec 12.1
    """
    backtest = VaRBacktesting(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        var_forecast=var_forecast,
        pnl_actual=None,  # Will be filled EOD
        is_exception=None,
        created_at=datetime.utcnow(),
    )
    
    session.add(backtest)
    await session.commit()
    
    logger.info(
        "var_forecast_recorded",
        portfolio_id=portfolio_id,
        date=as_of_date,
        var_forecast=var_forecast,
    )


async def record_actual_pnl(
    session: AsyncSession,
    portfolio_id: int,
    as_of_date: date,
    pnl_actual: float,
) -> bool:
    """
    Evening: record actual P&L and check for exception
    Per techspec 12.1
    
    Returns:
        True if exception occurred (P&L < -VaR)
    """
    # Find today's backtest record
    stmt = select(VaRBacktesting).where(
        VaRBacktesting.portfolio_id == portfolio_id,
        VaRBacktesting.as_of_date == as_of_date,
    )
    result = await session.execute(stmt)
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        logger.error(
            "var_backtest_not_found",
            portfolio_id=portfolio_id,
            date=as_of_date,
        )
        return False
    
    # Update with actual P&L
    backtest.pnl_actual = pnl_actual
    
    # Check for exception
    # Exception: actual loss exceeds VaR forecast
    is_exception = pnl_actual < -abs(backtest.var_forecast)
    backtest.is_exception = is_exception
    
    await session.commit()
    
    logger.info(
        "var_backtest_updated",
        portfolio_id=portfolio_id,
        date=as_of_date,
        pnl_actual=pnl_actual,
        var_forecast=backtest.var_forecast,
        is_exception=is_exception,
    )
    
    return is_exception


async def calc_exception_rate(
    session: AsyncSession,
    portfolio_id: int,
    window_days: int = 250,
) -> dict:
    """
    Calculate exception rate over rolling window
    Per techspec 12.2 - Traffic Light approach
    
    Returns:
        {
            'total_days': int,
            'exceptions': int,
            'exception_rate': float,
            'traffic_light': str  # GREEN, YELLOW, RED
        }
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=window_days)
    
    # Get backtesting records
    stmt = select(VaRBacktesting).where(
        VaRBacktesting.portfolio_id == portfolio_id,
        VaRBacktesting.as_of_date >= start_date,
        VaRBacktesting.as_of_date <= end_date,
        VaRBacktesting.pnl_actual.is_not(None),
    ).order_by(VaRBacktesting.as_of_date.desc())
    
    result = await session.execute(stmt)
    records = list(result.scalars().all())
    
    total_days = len(records)
    exceptions = sum(1 for r in records if r.is_exception)
    
    if total_days == 0:
        return {
            'total_days': 0,
            'exceptions': 0,
            'exception_rate': 0.0,
            'traffic_light': 'UNKNOWN',
        }
    
    exception_rate = exceptions / total_days
    
    # Basel Traffic Light approach (for 95% VaR)
    # Per techspec 12.2:
    # 0-4 exceptions → Green (model OK)
    # 5-9 → Yellow (review)
    # 10+ → Red (model rejected, multiplier ↑)
    if exceptions <= 4:
        traffic_light = 'GREEN'
    elif exceptions <= 9:
        traffic_light = 'YELLOW'
    else:
        traffic_light = 'RED'
    
    logger.info(
        "exception_rate_calculated",
        portfolio_id=portfolio_id,
        total_days=total_days,
        exceptions=exceptions,
        exception_rate=exception_rate,
        traffic_light=traffic_light,
    )
    
    return {
        'total_days': total_days,
        'exceptions': exceptions,
        'exception_rate': exception_rate,
        'traffic_light': traffic_light,
    }


async def get_var_multiplier(
    session: AsyncSession,
    portfolio_id: int,
) -> float:
    """
    Determine VaR multiplier based on backtesting performance
    Per techspec 12.2
    
    Returns:
        Multiplier: 3.0 (green), 3.4 (yellow), 3.85 (red), 4.0 (red with many exceptions)
    """
    stats = await calc_exception_rate(session, portfolio_id, window_days=250)
    
    traffic_light = stats['traffic_light']
    exceptions = stats['exceptions']
    
    # Basel multipliers
    if traffic_light == 'GREEN':
        return 3.0
    elif traffic_light == 'YELLOW':
        # 3.0 + 0.4 = 3.4 for 5 exceptions
        # Scale up to 3.85 for 9 exceptions
        if exceptions <= 5:
            return 3.4
        elif exceptions <= 7:
            return 3.6
        else:
            return 3.8
    else:  # RED
        if exceptions >= 15:
            return 4.0
        else:
            return 3.85
