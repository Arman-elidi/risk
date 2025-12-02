"""
Risk Engine Service - интеграция risk-core с БД
Основной модуль для расчёта рисков портфеля
"""
from datetime import datetime, date
from typing import List, Dict, Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

# Import risk-core
import sys
sys.path.insert(0, '/Users/armanamanbaev/Documents/RISK/risk-core')
from risk_core import aggregate_portfolio_risks
from risk_core.models import (
    BondPosition,
    DerivativePosition,
    InstrumentType,
    DayCountConvention,
)

from app.db.models import (
    Portfolio,
    Position,
    MarketDataSnapshot,
    YieldCurve,
    VolSurface,
    RiskSnapshot,
    Counterparty,
)
from app.schemas.risk import (
    CalculationRequest,
    CalculationResponse,
    RiskSnapshot as RiskSnapshotSchema,
)
from app.services.alert_engine import generate_alerts, save_alerts

logger = structlog.get_logger()

# In-memory store для расчётов (заменить на Redis в продакшене)
_CALCULATIONS = {}
_SNAPSHOTS = {}


async def load_bond_positions(
    session: AsyncSession,
    portfolio_id: int,
    as_of_date: date,
) -> List[BondPosition]:
    """Load bond positions from database and convert to risk-core models"""
    result = await session.execute(
        select(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.status == 'ACTIVE',
            Position.instrument_type == 'BOND',
        )
    )
    positions = result.scalars().all()
    
    bond_positions = []
    for pos in positions:
        # Get market data
        mkt_result = await session.execute(
            select(MarketDataSnapshot).where(
                MarketDataSnapshot.isin == pos.isin,
                MarketDataSnapshot.snapshot_date == as_of_date,
            ).order_by(MarketDataSnapshot.snapshot_time.desc()).limit(1)
        )
        mkt_data = mkt_result.scalar_one_or_none()
        
        if not mkt_data:
            logger.warning("market_data_missing", isin=pos.isin)
            continue
        
        bond = BondPosition(
            isin=pos.isin,
            nominal=1000.0,  # Standard
            quantity=pos.quantity,
            coupon=pos.coupon or 0.0,
            coupon_frequency=pos.coupon_frequency or 2,
            maturity_date=pos.maturity_date,
            issue_date=pos.trade_date or date(2020, 1, 1),
            clean_price=mkt_data.price or 100.0,
            ytm=mkt_data.yield_pct or 0.05,
            day_count=DayCountConvention.ACT_365,
            issuer_id=pos.issuer_id,
            currency='USD',
            rating=None,
        )
        bond_positions.append(bond)
    
    logger.info("loaded_bond_positions", count=len(bond_positions))
    return bond_positions


async def load_derivative_positions(
    session: AsyncSession,
    portfolio_id: int,
) -> List[DerivativePosition]:
    """Load derivative positions"""
    result = await session.execute(
        select(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.status == 'ACTIVE',
            Position.instrument_type.in_(['FX_FORWARD', 'FX_OPTION', 'IR_SWAP']),
        )
    )
    positions = result.scalars().all()
    
    deriv_positions = []
    for pos in positions:
        # Map instrument type
        if pos.instrument_type == 'FX_FORWARD':
            inst_type = InstrumentType.FX_FORWARD
        elif pos.instrument_type == 'FX_OPTION':
            inst_type = InstrumentType.FX_OPTION
        elif pos.instrument_type == 'IR_SWAP':
            inst_type = InstrumentType.IR_SWAP
        else:
            continue
        
        deriv = DerivativePosition(
            instrument_id=pos.instrument_id or f"DERIV_{pos.id}",
            instrument_type=inst_type,
            notional=pos.notional or 0.0,
            direction=pos.direction or 'LONG',
            underlying=pos.underlying or 'EURUSD',
            trade_date=pos.trade_date or date.today(),
            maturity_date=pos.maturity_date or date.today(),
            counterparty_id=pos.counterparty_id or 1,
            mtm=0.0,  # TODO: Calculate MtM
            strike=pos.strike,
            option_type=pos.option_type,
        )
        deriv_positions.append(deriv)
    
    logger.info("loaded_derivative_positions", count=len(deriv_positions))
    return deriv_positions


async def load_pnl_history(
    session: AsyncSession,
    portfolio_id: int,
    days: int = 250,
) -> List[float]:
    """Load historical P&L for VaR calculation"""
    # TODO: Implement from var_backtesting or calculated from risk_snapshots
    # For now, return mock data
    import numpy as np
    np.random.seed(portfolio_id)
    pnl = list(np.random.normal(loc=0, scale=50_000, size=days))
    return pnl


async def calculate_portfolio_risks(
    session: AsyncSession,
    portfolio_id: int,
    as_of_date: date,
    req: CalculationRequest,
) -> RiskSnapshot:
    """
    Главная функция расчёта рисков портфеля
    
    Шаги:
    1. Загрузить позиции из БД
    2. Загрузить market data
    3. Вызвать risk-core.aggregate_portfolio_risks
    4. Сохранить результат в risk_snapshots
    5. Вернуть RiskSnapshot
    """
    logger.info("calculate_portfolio_risks_started", portfolio_id=portfolio_id, date=as_of_date)
    
    try:
        # 1. Load positions
        bond_positions = await load_bond_positions(session, portfolio_id, as_of_date)
        deriv_positions = await load_derivative_positions(session, portfolio_id)
        
        # 2. Load P&L history
        pnl_history = await load_pnl_history(session, portfolio_id)
        
        # 3. Prepare credit exposures (simplified)
        credit_exposures = []
        for bond in bond_positions:
            credit_exposures.append({
                'exposure': bond.nominal * bond.quantity * (bond.clean_price / 100.0),
                'rating': 'BBB',
                'seniority': 'SENIOR',
            })
        
        # 4. Group derivatives by counterparty
        counterparty_derivatives = {}
        for deriv in deriv_positions:
            cpty_id = deriv.counterparty_id
            if cpty_id not in counterparty_derivatives:
                counterparty_derivatives[cpty_id] = []
            counterparty_derivatives[cpty_id].append(deriv)
        
        # 5. Prepare liquidity positions
        liquidity_positions = []
        for bond in bond_positions:
            liquidity_positions.append({
                'market_value': bond.nominal * bond.quantity * (bond.clean_price / 100.0),
                'bid_ask_spread_bps': 20.0,
                'liquidity_score': 0.75,
            })
        
        # 6. Call risk-core
        result = aggregate_portfolio_risks(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            bond_positions=bond_positions,
            derivative_positions=deriv_positions,
            pnl_history=pnl_history,
            credit_exposures=credit_exposures,
            counterparty_derivatives=counterparty_derivatives,
            counterparty_ratings={1: 'A', 2: 'BBB'},
            liquidity_positions=liquidity_positions,
            hqla=1_000_000.0,
            net_cash_outflows_30d=800_000.0,
            assets_by_bucket={'0-7d': 500_000, '7-30d': 300_000},
            liabilities_by_bucket={'0-7d': 400_000, '7-30d': 400_000},
            aum_avg=10_000_000.0,
            client_money_held_avg=5_000_000.0,
            own_funds=1_500_000.0,
            wwr_alpha=req.wwr_alpha or 1.0,
            engine_version='0.1.0',
        )
        
        # 7. Save to database
        snapshot = RiskSnapshot(
            portfolio_id=portfolio_id,
            snapshot_date=as_of_date,
            calculation_timestamp=datetime.utcnow(),
            calculation_status='COMPLETED',
            engine_version='0.1.0',
        )
        
        # Map bond metrics
        if result.bond_metrics:
            snapshot.dv01_total = result.bond_metrics.total_dv01
            snapshot.duration = result.bond_metrics.weighted_avg_duration
            snapshot.convexity = result.bond_metrics.convexity
        
        # Map VaR metrics
        if result.var_metrics:
            snapshot.var_1d_95 = result.var_metrics.var_1d_95
            snapshot.stressed_var = result.var_metrics.stressed_var
        
        # Map credit metrics
        if result.credit_metrics:
            snapshot.total_exposure = result.credit_metrics.total_exposure
            snapshot.credit_var = result.credit_metrics.credit_var
            snapshot.expected_loss = result.credit_metrics.expected_loss
        
        # Map CCR metrics
        if result.ccr_metrics:
            snapshot.pfe_current = sum(m.pfe_current for m in result.ccr_metrics)
            snapshot.pfe_peak = max(m.pfe_peak for m in result.ccr_metrics)
            snapshot.ead_total = sum(m.ead_ccr for m in result.ccr_metrics)
        
        # Map liquidity
        if result.liquidity_metrics:
            snapshot.liquidation_cost_1d = result.liquidity_metrics.liquidation_cost_1d
            snapshot.liquidation_cost_5d = result.liquidity_metrics.liquidation_cost_5d
            snapshot.liquidity_score = result.liquidity_metrics.liquidity_score
            snapshot.lcr_ratio = result.liquidity_metrics.lcr_ratio
            snapshot.funding_gap_short_term = result.liquidity_metrics.funding_gap_short_term
        
        # Map capital
        if result.capital_metrics:
            snapshot.k_npr = result.capital_metrics.k_npr
            snapshot.k_aum = result.capital_metrics.k_aum
            snapshot.k_cmh = result.capital_metrics.k_cmh
            snapshot.k_coh = result.capital_metrics.k_coh
            snapshot.total_k_req = result.capital_metrics.total_k_req
            snapshot.own_funds = result.capital_metrics.own_funds
            snapshot.capital_ratio = result.capital_metrics.capital_ratio
        
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        
        # 8. Generate and save alerts
        alerts = await generate_alerts(session, snapshot)
        await save_alerts(session, alerts)
        
        logger.info("calculate_portfolio_risks_completed", 
                   snapshot_id=snapshot.id,
                   calc_time=result.calculation_time_seconds,
                   alerts_count=len(alerts))
        
        return snapshot
        
    except Exception as e:
        logger.error("calculate_portfolio_risks_failed", error=str(e), exc_info=True)
        raise


async def trigger_calculation(
    session: AsyncSession,
    portfolio_id: int,
    req: CalculationRequest,
) -> CalculationResponse:
    """Trigger on-demand risk calculation"""
    calc_id = f"calc_{uuid4().hex[:8]}"
    as_of_date = req.as_of_date or date.today()
    
    logger.info("trigger_calculation", calc_id=calc_id, portfolio_id=portfolio_id)
    
    # Sync calculation (в продакшене использовать Celery для async)
    snapshot = await calculate_portfolio_risks(session, portfolio_id, as_of_date, req)
    
    _CALCULATIONS[calc_id] = {
        'status': 'COMPLETED',
        'snapshot_id': snapshot.id,
        'started_at': datetime.utcnow(),
        'finished_at': datetime.utcnow(),
    }
    
    return CalculationResponse(
        calculation_id=calc_id,
        calculation_status='COMPLETED',
        risk_snapshot_id=str(snapshot.id),
        eta_seconds=None,
    )


def get_calculation(calculation_id: str):
    """Get calculation status"""
    return _CALCULATIONS.get(calculation_id)


async def get_snapshot(session: AsyncSession, snapshot_id: int) -> RiskSnapshot | None:
    """Get risk snapshot by ID"""
    result = await session.execute(
        select(RiskSnapshot).where(RiskSnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()


async def list_snapshots(
    session: AsyncSession,
    portfolio_id: int | None = None,
    limit: int = 50,
) -> List[RiskSnapshot]:
    """List risk snapshots"""
    query = select(RiskSnapshot).order_by(RiskSnapshot.snapshot_date.desc())
    
    if portfolio_id:
        query = query.where(RiskSnapshot.portfolio_id == portfolio_id)
    
    query = query.limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())
