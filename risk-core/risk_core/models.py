"""
Data models for risk calculations
Using dataclasses for pure Python (no Pydantic dependency)
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict
from enum import Enum


class InstrumentType(Enum):
    BOND = "BOND"
    FX_FORWARD = "FX_FORWARD"
    FX_OPTION = "FX_OPTION"
    IR_SWAP = "IR_SWAP"
    IR_CAP = "IR_CAP"
    IR_FLOOR = "IR_FLOOR"
    SWAPTION = "SWAPTION"


class DayCountConvention(Enum):
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    ACT_ACT = "ACT/ACT"
    THIRTY_360 = "30/360"
    THIRTY_E_360 = "30E/360"


@dataclass
class BondPosition:
    """Bond position with all attributes for risk calculation"""
    isin: str
    nominal: float
    quantity: float
    coupon: float  # Annual coupon rate (e.g., 0.05 for 5%)
    coupon_frequency: int  # Payments per year: 1, 2, 4
    maturity_date: date
    issue_date: date
    clean_price: float  # Market price (% of par)
    ytm: float  # Yield to maturity
    day_count: DayCountConvention = DayCountConvention.ACT_365
    issuer_id: Optional[int] = None
    currency: str = "USD"
    seniority: str = "SENIOR"
    rating: Optional[str] = None


@dataclass
class DerivativePosition:
    """Generic derivative position"""
    instrument_id: str
    instrument_type: InstrumentType
    notional: float
    direction: str  # LONG/SHORT, PAY/RECEIVE
    underlying: str
    trade_date: date
    maturity_date: date
    counterparty_id: int
    mtm: float  # Mark-to-market value
    currency: str = "USD"
    
    # Option-specific
    strike: Optional[float] = None
    option_type: Optional[str] = None  # CALL/PUT
    exercise_type: Optional[str] = None  # EUROPEAN/AMERICAN
    
    # IR Swap-specific
    fixed_rate: Optional[float] = None
    floating_index: Optional[str] = None


@dataclass
class MarketData:
    """Market data snapshot for one instrument"""
    instrument_id: str
    as_of_date: date
    price: Optional[float] = None
    yield_pct: Optional[float] = None
    spread_bps: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    implied_vol: Optional[float] = None
    fx_rate: Optional[float] = None
    credit_spread_bps: Optional[float] = None
    cds_spread_5y_bps: Optional[float] = None
    recovery_rate: Optional[float] = None
    liquidity_score: Optional[float] = None


@dataclass
class YieldCurve:
    """Yield curve for discounting"""
    curve_id: str
    currency: str
    as_of_date: date
    tenors: List[float]  # Years: [0.25, 0.5, 1, 2, 5, 10, 30]
    rates: List[float]  # Zero rates


@dataclass
class VolSurface:
    """Volatility surface for options"""
    surface_id: str
    underlying: str
    as_of_date: date
    strikes: List[float]
    expiries: List[float]  # Years
    vols: List[List[float]]  # 2D grid


@dataclass
class BondMetrics:
    """Calculated bond metrics"""
    position_id: str
    dv01: float
    modified_duration: float
    macaulay_duration: float
    convexity: float
    market_value: float
    accrued_interest: float


@dataclass
class PortfolioBondMetrics:
    """Aggregated bond portfolio metrics"""
    total_market_value: float
    total_dv01: float
    weighted_avg_duration: float
    weighted_avg_maturity: float
    weighted_avg_rating: Optional[str] = None
    convexity: float = 0.0


@dataclass
class VaRMetrics:
    """VaR calculation results"""
    var_1d_95: float
    stressed_var: float
    var_10d_99: Optional[float] = None


@dataclass
class CreditMetrics:
    """Credit risk metrics"""
    total_exposure: float
    expected_loss: float
    credit_var: float
    pd: float  # Probability of default
    lgd: float  # Loss given default
    ead: float  # Exposure at default


@dataclass
class CCRMetrics:
    """Counterparty credit risk metrics"""
    counterparty_id: int
    current_exposure: float
    pfe_current: float
    pfe_peak: float
    ead_ccr: float
    wwr_alpha: float = 1.0


@dataclass
class LiquidityMetrics:
    """Liquidity risk metrics"""
    liquidation_cost_1d: float
    liquidation_cost_5d: float
    liquidity_score: float
    lcr_ratio: float
    funding_gap_short_term: float


@dataclass
class CapitalMetrics:
    """Capital adequacy (IFR K-factors)"""
    k_npr: float  # Net Position Risk
    k_aum: float  # Assets Under Management
    k_cmh: float  # Client Money Held
    k_coh: float  # Client Orders Handled
    total_k_req: float
    own_funds: float
    capital_ratio: float


@dataclass
class PortfolioRiskResult:
    """Complete portfolio risk snapshot"""
    portfolio_id: int
    as_of_date: date
    engine_version: str
    
    # Aggregated metrics
    bond_metrics: Optional[PortfolioBondMetrics] = None
    var_metrics: Optional[VaRMetrics] = None
    credit_metrics: Optional[CreditMetrics] = None
    ccr_metrics: Optional[List[CCRMetrics]] = None
    liquidity_metrics: Optional[LiquidityMetrics] = None
    capital_metrics: Optional[CapitalMetrics] = None
    
    calculation_time_seconds: float = 0.0
