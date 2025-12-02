from datetime import datetime, date
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class CalculationModules(BaseModel):
    bond: bool = True
    derivatives: bool = True
    credit: bool = True
    ccr: bool = True
    cva: bool = True
    liquidity: bool = True
    capital: bool = True

class CalculationRequest(BaseModel):
    as_of_date: Optional[date] = None
    use_cached: bool = True
    modules: Optional[CalculationModules] = None
    scenarios: Optional[List[str]] = None
    wwr_alpha: Optional[float] = None

class CalculationResponse(BaseModel):
    calculation_id: str
    calculation_status: str
    risk_snapshot_id: Optional[str] = None
    eta_seconds: Optional[int] = None

class MarketMetrics(BaseModel):
    var_1d_95: float
    stressed_var: float
    dv01_total: float
    duration: float
    convexity: float

class CreditMetrics(BaseModel):
    total_exposure: float
    credit_var: float
    cva_total: float
    expected_loss: float

class CCRMetrics(BaseModel):
    pfe_current: float
    pfe_peak: float
    ead_total: float

class LiquidityMetrics(BaseModel):
    liquidation_cost_1d: float
    liquidation_cost_5d: float
    liquidity_score: float
    lcr_ratio: float
    funding_gap_short_term: float

class CapitalMetrics(BaseModel):
    k_npr: float
    k_aum: float
    k_cmh: float
    k_coh: float
    total_k_req: float
    own_funds: float
    capital_ratio: float

class AlertsSummary(BaseModel):
    GREEN: int = 0
    YELLOW: int = 0
    RED: int = 0
    CRITICAL: int = 0

class RiskSnapshot(BaseModel):
    risk_snapshot_id: str
    portfolio_id: int
    snapshot_date: date
    calculation_timestamp: datetime
    calculation_status: str
    market: MarketMetrics
    credit: CreditMetrics
    ccr: CCRMetrics
    liquidity: LiquidityMetrics
    capital: CapitalMetrics
    alerts_summary: AlertsSummary = Field(default_factory=AlertsSummary)
    error_message: Optional[str] = None

class SnapshotHeader(BaseModel):
    risk_snapshot_id: str
    portfolio_id: int
    snapshot_date: date
    calculation_status: str
