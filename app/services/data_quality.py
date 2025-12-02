"""
Data Quality Framework
Per techspec section 13.2
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.models import DataQualityIssue

logger = structlog.get_logger()


class DQRule(str, Enum):
    """Data Quality Rules per techspec 13.2"""
    # Price Data (DQ-01 to DQ-08)
    DQ_01_PRICE_JUMP = "DQ-01"  # Price jump >10% d/d
    DQ_02_ZERO_PRICE = "DQ-02"  # Price = 0 or NULL
    DQ_03_BID_ASK = "DQ-03"  # Bid > Ask
    DQ_04_SPREAD_WIDE = "DQ-04"  # Bid-ask spread > 500 bps
    DQ_05_STALE_PRICE = "DQ-05"  # No update >5 days
    DQ_06_ZERO_VOLUME = "DQ-06"  # Volume = 0 for >3 days
    DQ_07_YIELD_OUTLIER = "DQ-07"  # Yield outside [0, 25%]
    DQ_08_SPREAD_OUTLIER = "DQ-08"  # Spread > 2000 bps (HY)
    
    # FX Data (DQ-10 to DQ-12)
    DQ_10_MISSING_FX = "DQ-10"  # Missing FX rate
    DQ_11_FX_JUMP = "DQ-11"  # FX move >5% d/d
    DQ_12_FX_ARBITRAGE = "DQ-12"  # Triangular arbitrage violation
    
    # Curves (DQ-20 to DQ-22)
    DQ_20_CURVE_INVERSION = "DQ-20"  # Yield curve inversion
    DQ_21_MISSING_TENORS = "DQ-21"  # Missing key tenors
    DQ_22_CURVE_SHIFT = "DQ-22"  # Curve shift >100 bps d/d
    
    # Reference & Positions (DQ-30 to DQ-43)
    DQ_30_RATING_CHANGE = "DQ-30"  # Rating change >3 notches d/d
    DQ_31_MISSING_ISSUER = "DQ-31"  # Unknown issuer
    DQ_32_MATURITY_MISMATCH = "DQ-32"  # Maturity < today
    DQ_33_DUPLICATE_POSITION = "DQ-33"  # Duplicate ISIN in portfolio
    DQ_34_TRADE_DATE_FUTURE = "DQ-34"  # Trade date > today
    DQ_35_MTM_OUTLIER = "DQ-35"  # MtM change >30% d/d


class DQSeverity(str, Enum):
    """Data quality issue severity"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DQCheckResult:
    """Result of a DQ check"""
    rule: DQRule
    severity: DQSeverity
    passed: bool
    source: str  # Bloomberg, Refinitiv, BackOffice, etc.
    instrument_id: Optional[str] = None
    snapshot_id: Optional[int] = None
    details: Optional[str] = None


async def check_price_jump(
    current_price: float,
    previous_price: float,
    instrument_id: str,
    threshold_pct: float = 10.0,
) -> Optional[DQCheckResult]:
    """
    DQ-01: Check for price jump >10% d/d
    """
    if previous_price == 0:
        return None
    
    change_pct = abs((current_price - previous_price) / previous_price) * 100
    
    if change_pct > threshold_pct:
        return DQCheckResult(
            rule=DQRule.DQ_01_PRICE_JUMP,
            severity=DQSeverity.WARNING,
            passed=False,
            source="MarketData",
            instrument_id=instrument_id,
            details=f"Price jump: {change_pct:.2f}% (current={current_price}, prev={previous_price})",
        )
    
    return DQCheckResult(
        rule=DQRule.DQ_01_PRICE_JUMP,
        severity=DQSeverity.INFO,
        passed=True,
        source="MarketData",
        instrument_id=instrument_id,
    )


async def check_zero_price(
    price: Optional[float],
    instrument_id: str,
) -> Optional[DQCheckResult]:
    """
    DQ-02: Price = 0 or NULL
    """
    if price is None or price == 0:
        return DQCheckResult(
            rule=DQRule.DQ_02_ZERO_PRICE,
            severity=DQSeverity.ERROR,
            passed=False,
            source="MarketData",
            instrument_id=instrument_id,
            details=f"Price is {price}",
        )
    
    return DQCheckResult(
        rule=DQRule.DQ_02_ZERO_PRICE,
        severity=DQSeverity.INFO,
        passed=True,
        source="MarketData",
        instrument_id=instrument_id,
    )


async def check_bid_ask(
    bid: float,
    ask: float,
    instrument_id: str,
) -> Optional[DQCheckResult]:
    """
    DQ-03: Bid > Ask
    """
    if bid > ask:
        return DQCheckResult(
            rule=DQRule.DQ_03_BID_ASK,
            severity=DQSeverity.ERROR,
            passed=False,
            source="MarketData",
            instrument_id=instrument_id,
            details=f"Bid ({bid}) > Ask ({ask})",
        )
    
    return DQCheckResult(
        rule=DQRule.DQ_03_BID_ASK,
        severity=DQSeverity.INFO,
        passed=True,
        source="MarketData",
        instrument_id=instrument_id,
    )


async def check_spread_wide(
    bid: float,
    ask: float,
    instrument_id: str,
    threshold_bps: float = 500.0,
) -> Optional[DQCheckResult]:
    """
    DQ-04: Bid-ask spread > 500 bps
    """
    mid = (bid + ask) / 2
    if mid == 0:
        return None
    
    spread_bps = ((ask - bid) / mid) * 10000
    
    if spread_bps > threshold_bps:
        return DQCheckResult(
            rule=DQRule.DQ_04_SPREAD_WIDE,
            severity=DQSeverity.WARNING,
            passed=False,
            source="MarketData",
            instrument_id=instrument_id,
            details=f"Spread: {spread_bps:.2f} bps (threshold: {threshold_bps})",
        )
    
    return DQCheckResult(
        rule=DQRule.DQ_04_SPREAD_WIDE,
        severity=DQSeverity.INFO,
        passed=True,
        source="MarketData",
        instrument_id=instrument_id,
    )


async def save_dq_issue(
    session: AsyncSession,
    result: DQCheckResult,
) -> None:
    """
    Save DQ issue to database
    Per techspec 13.2: Workflow -> data_quality_issues table
    """
    if result.passed:
        return  # Only save failures
    
    issue = DataQualityIssue(
        issue_type=result.rule.value,
        severity=result.severity.value,
        source=result.source,
        instrument_id=result.instrument_id,
        snapshot_id=result.snapshot_id,
        description=result.details or "",
        created_at=datetime.utcnow(),
        resolved_at=None,
    )
    
    session.add(issue)
    await session.commit()
    
    logger.warning(
        "dq_issue_detected",
        rule=result.rule.value,
        severity=result.severity.value,
        instrument_id=result.instrument_id,
        details=result.details,
    )


async def run_dq_checks(
    session: AsyncSession,
    market_data: List[dict],
) -> List[DQCheckResult]:
    """
    Run all DQ checks on market data
    
    Args:
        market_data: List of market data records
    
    Returns:
        List of DQ check results
    """
    results = []
    
    for data in market_data:
        instrument_id = data.get('instrument_id')
        
        # Check zero price
        price_result = await check_zero_price(
            data.get('price'),
            instrument_id,
        )
        if price_result:
            results.append(price_result)
            await save_dq_issue(session, price_result)
        
        # Check bid-ask
        bid = data.get('bid')
        ask = data.get('ask')
        if bid and ask:
            bid_ask_result = await check_bid_ask(bid, ask, instrument_id)
            if bid_ask_result:
                results.append(bid_ask_result)
                await save_dq_issue(session, bid_ask_result)
            
            # Check spread
            spread_result = await check_spread_wide(bid, ask, instrument_id)
            if spread_result:
                results.append(spread_result)
                await save_dq_issue(session, spread_result)
        
        # Check price jump (if previous price available)
        prev_price = data.get('previous_price')
        if prev_price:
            jump_result = await check_price_jump(
                data.get('price', 0),
                prev_price,
                instrument_id,
            )
            if jump_result:
                results.append(jump_result)
                await save_dq_issue(session, jump_result)
    
    logger.info(
        "dq_checks_completed",
        total_checks=len(results),
        failed_checks=sum(1 for r in results if not r.passed),
    )
    
    return results
