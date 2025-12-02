from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import auth_bearer
from app.db.session import get_db
from app.schemas.risk import (
    CalculationRequest,
    CalculationResponse,
    RiskSnapshot as RiskSnapshotSchema,
    SnapshotHeader,
    MarketMetrics,
    CreditMetrics,
    CCRMetrics,
    LiquidityMetrics,
    CapitalMetrics,
    AlertsSummary,
)
from app.services.risk_engine import (
    trigger_calculation,
    get_calculation,
    get_snapshot,
    list_snapshots,
)

router = APIRouter()


def map_snapshot_to_schema(snapshot) -> RiskSnapshotSchema:
    """Map DB model to Pydantic schema"""
    return RiskSnapshotSchema(
        risk_snapshot_id=str(snapshot.id),
        portfolio_id=snapshot.portfolio_id,
        snapshot_date=snapshot.snapshot_date,
        calculation_timestamp=snapshot.calculation_timestamp,
        calculation_status=snapshot.calculation_status,
        market=MarketMetrics(
            var_1d_95=snapshot.var_1d_95 or 0.0,
            stressed_var=snapshot.stressed_var or 0.0,
            dv01_total=snapshot.dv01_total or 0.0,
            duration=snapshot.duration or 0.0,
            convexity=snapshot.convexity or 0.0,
        ),
        credit=CreditMetrics(
            total_exposure=snapshot.total_exposure or 0.0,
            credit_var=snapshot.credit_var or 0.0,
            cva_total=snapshot.cva_total or 0.0,
            expected_loss=snapshot.expected_loss or 0.0,
        ),
        ccr=CCRMetrics(
            pfe_current=snapshot.pfe_current or 0.0,
            pfe_peak=snapshot.pfe_peak or 0.0,
            ead_total=snapshot.ead_total or 0.0,
        ),
        liquidity=LiquidityMetrics(
            liquidation_cost_1d=snapshot.liquidation_cost_1d or 0.0,
            liquidation_cost_5d=snapshot.liquidation_cost_5d or 0.0,
            liquidity_score=snapshot.liquidity_score or 0.0,
            lcr_ratio=snapshot.lcr_ratio or 0.0,
            funding_gap_short_term=snapshot.funding_gap_short_term or 0.0,
        ),
        capital=CapitalMetrics(
            k_npr=snapshot.k_npr or 0.0,
            k_aum=snapshot.k_aum or 0.0,
            k_cmh=snapshot.k_cmh or 0.0,
            k_coh=snapshot.k_coh or 0.0,
            total_k_req=snapshot.total_k_req or 0.0,
            own_funds=snapshot.own_funds or 0.0,
            capital_ratio=snapshot.capital_ratio or 0.0,
        ),
        alerts_summary=AlertsSummary(),  # TODO: aggregate from alerts table
        error_message=snapshot.error_message,
    )


@router.post("/portfolios/{portfolio_id}/risk/calculate", response_model=CalculationResponse)
async def calculate_portfolio_risk(
    portfolio_id: int,
    req: CalculationRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth_bearer),
):
    """Trigger on-demand risk calculation for portfolio"""
    return await trigger_calculation(db, portfolio_id, req)


@router.get("/calculations/{calculation_id}")
async def get_calculation_status(calculation_id: str, user=Depends(auth_bearer)):
    """Get calculation status by ID"""
    calc = get_calculation(calculation_id)
    if not calc:
        raise HTTPException(
            status_code=404,
            detail={
                "status": 404,
                "code": "NOT_FOUND",
                "message": f"Calculation {calculation_id} not found",
            },
        )
    return calc


@router.get("/risk_snapshots/{risk_snapshot_id}", response_model=RiskSnapshotSchema)
async def get_risk_snapshot(
    risk_snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth_bearer),
):
    """Get risk snapshot by ID"""
    snap = await get_snapshot(db, risk_snapshot_id)
    if not snap:
        raise HTTPException(
            status_code=404,
            detail={
                "status": 404,
                "code": "NOT_FOUND",
                "message": f"Snapshot {risk_snapshot_id} not found",
            },
        )
    return map_snapshot_to_schema(snap)


@router.get("/risk_snapshots")
async def list_risk_snapshots(
    portfolio_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth_bearer),
):
    """List risk snapshots with optional portfolio filter"""
    snapshots = await list_snapshots(db, portfolio_id)
    return [map_snapshot_to_schema(s) for s in snapshots]
