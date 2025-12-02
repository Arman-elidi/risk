"""
Stress Testing Framework
Per techspec section 11
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import date
from enum import Enum


class StressScenario(str, Enum):
    """Stress scenarios per techspec 11.1"""
    # Interest Rate Shocks
    IR_01 = "IR_01"  # +200 bps parallel
    IR_02 = "IR_02"  # -100 bps parallel
    IR_03 = "IR_03"  # Steepening (short +50, long +150)
    IR_04 = "IR_04"  # Flattening (short +150, long +50)
    IR_05 = "IR_05"  # Twist (5Y pivot)
    
    # Credit Spread Shocks
    CS_01 = "CS_01"  # +100 bps all corporates
    CS_02 = "CS_02"  # +200 bps HY (BB and below)
    CS_03 = "CS_03"  # +50 bps IG (BBB and above)
    CS_04 = "CS_04"  # +300 bps single-name (top-5)
    
    # FX Shocks
    FX_01 = "FX_01"  # USD +10%
    FX_02 = "FX_02"  # USD -10%
    FX_03 = "FX_03"  # EUR/USD -15%
    FX_04 = "FX_04"  # EM FX crisis -25%
    
    # Volatility Shocks
    VOL_01 = "VOL_01"  # vol ×1.2
    VOL_02 = "VOL_02"  # vol ×1.4
    VOL_03 = "VOL_03"  # smile flattening
    VOL_04 = "VOL_04"  # skew shift
    
    # Combined/Historical
    CRISIS_2008 = "CRISIS_2008"
    CRISIS_2020 = "CRISIS_2020"
    TAPER_2013 = "TAPER_2013"
    
    # Liquidity Stress
    LIQ_01 = "LIQ_01"  # bid-ask ×3
    LIQ_02 = "LIQ_02"  # market depth -50%
    LIQ_03 = "LIQ_03"  # deposits -20%
    LIQ_04 = "LIQ_04"  # simultaneous margin calls


@dataclass
class StressShock:
    """Definition of a stress shock"""
    scenario: StressScenario
    description: str
    
    # IR shocks (basis points)
    ir_parallel_shock_bps: Optional[float] = None
    ir_short_shock_bps: Optional[float] = None
    ir_long_shock_bps: Optional[float] = None
    
    # Credit spread shocks (basis points)
    credit_spread_shock_bps: Optional[float] = None
    credit_hy_shock_bps: Optional[float] = None
    credit_ig_shock_bps: Optional[float] = None
    
    # FX shocks (percentage)
    fx_shock_pct: Optional[float] = None
    
    # Vol shocks (multiplier)
    vol_multiplier: Optional[float] = None
    
    # Liquidity shocks
    bid_ask_multiplier: Optional[float] = None
    market_depth_shock_pct: Optional[float] = None
    deposit_runoff_pct: Optional[float] = None


@dataclass
class StressResult:
    """Results of stress test for a portfolio"""
    scenario: StressScenario
    portfolio_id: int
    as_of_date: date
    
    # P&L impact
    pnl_impact: float
    pnl_pct: float
    
    # Risk metrics changes
    delta_var: float
    delta_dv01: float
    delta_duration: float
    
    # Greeks changes (for derivatives)
    delta_greeks_delta: Optional[float] = None
    delta_greeks_gamma: Optional[float] = None
    delta_greeks_vega: Optional[float] = None
    
    # Capital impact
    delta_k_factors: Optional[float] = None
    delta_capital_ratio: Optional[float] = None
    
    # Liquidity impact
    delta_lcr: Optional[float] = None
    
    # Top contributors
    top_10_contributors: Optional[List[Dict]] = None


# Predefined scenarios per techspec 11.1
STRESS_SCENARIOS = {
    StressScenario.IR_01: StressShock(
        scenario=StressScenario.IR_01,
        description="Interest Rate Shock: +200 bps parallel",
        ir_parallel_shock_bps=200.0,
    ),
    StressScenario.IR_02: StressShock(
        scenario=StressScenario.IR_02,
        description="Interest Rate Shock: -100 bps parallel",
        ir_parallel_shock_bps=-100.0,
    ),
    StressScenario.IR_03: StressShock(
        scenario=StressScenario.IR_03,
        description="Interest Rate Shock: Steepening",
        ir_short_shock_bps=50.0,
        ir_long_shock_bps=150.0,
    ),
    StressScenario.IR_04: StressShock(
        scenario=StressScenario.IR_04,
        description="Interest Rate Shock: Flattening",
        ir_short_shock_bps=150.0,
        ir_long_shock_bps=50.0,
    ),
    StressScenario.CS_01: StressShock(
        scenario=StressScenario.CS_01,
        description="Credit Spread Shock: +100 bps all corporates",
        credit_spread_shock_bps=100.0,
    ),
    StressScenario.CS_02: StressShock(
        scenario=StressScenario.CS_02,
        description="Credit Spread Shock: +200 bps HY",
        credit_hy_shock_bps=200.0,
    ),
    StressScenario.CS_03: StressShock(
        scenario=StressScenario.CS_03,
        description="Credit Spread Shock: +50 bps IG",
        credit_ig_shock_bps=50.0,
    ),
    StressScenario.FX_01: StressShock(
        scenario=StressScenario.FX_01,
        description="FX Shock: USD +10%",
        fx_shock_pct=10.0,
    ),
    StressScenario.FX_02: StressShock(
        scenario=StressScenario.FX_02,
        description="FX Shock: USD -10%",
        fx_shock_pct=-10.0,
    ),
    StressScenario.VOL_01: StressShock(
        scenario=StressScenario.VOL_01,
        description="Volatility Shock: vol ×1.2",
        vol_multiplier=1.2,
    ),
    StressScenario.VOL_02: StressShock(
        scenario=StressScenario.VOL_02,
        description="Volatility Shock: vol ×1.4",
        vol_multiplier=1.4,
    ),
    StressScenario.LIQ_01: StressShock(
        scenario=StressScenario.LIQ_01,
        description="Liquidity Stress: bid-ask ×3",
        bid_ask_multiplier=3.0,
    ),
    StressScenario.LIQ_02: StressShock(
        scenario=StressScenario.LIQ_02,
        description="Liquidity Stress: market depth -50%",
        market_depth_shock_pct=-50.0,
    ),
}


def apply_ir_shock_to_bond(
    bond_dv01: float,
    shock_bps: float,
) -> float:
    """
    Apply IR shock to bond using DV01
    P&L = -DV01 × shock_bps / 100
    """
    pnl = -bond_dv01 * (shock_bps / 100.0)
    return pnl


def apply_credit_shock_to_bond(
    bond_spread_duration: float,
    market_value: float,
    shock_bps: float,
) -> float:
    """
    Apply credit spread shock using spread duration
    P&L = -Spread Duration × MV × shock_bps / 10000
    """
    pnl = -bond_spread_duration * market_value * (shock_bps / 10000.0)
    return pnl


def calc_stress_test(
    scenario: StressScenario,
    portfolio_metrics: Dict,
    positions_data: List[Dict],
) -> StressResult:
    """
    Run stress test for given scenario
    
    This is a simplified implementation per techspec 11.2
    Full implementation would reprice all positions under shocked scenarios
    """
    shock = STRESS_SCENARIOS.get(scenario)
    if not shock:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    total_pnl = 0.0
    
    # Apply IR shock
    if shock.ir_parallel_shock_bps:
        total_dv01 = portfolio_metrics.get('dv01_total', 0.0)
        pnl_ir = apply_ir_shock_to_bond(total_dv01, shock.ir_parallel_shock_bps)
        total_pnl += pnl_ir
    
    # Apply credit shock
    if shock.credit_spread_shock_bps:
        # Simplified: assume average spread duration
        total_mv = portfolio_metrics.get('total_market_value', 0.0)
        avg_spread_dur = portfolio_metrics.get('avg_spread_duration', 0.0)
        pnl_credit = apply_credit_shock_to_bond(avg_spread_dur, total_mv, shock.credit_spread_shock_bps)
        total_pnl += pnl_credit
    
    # Calculate percentage impact
    total_mv = portfolio_metrics.get('total_market_value', 1.0)
    pnl_pct = (total_pnl / total_mv) * 100 if total_mv > 0 else 0.0
    
    # Estimate VaR change (simplified)
    delta_var = abs(total_pnl) * 0.8  # Rough approximation
    
    return StressResult(
        scenario=scenario,
        portfolio_id=portfolio_metrics.get('portfolio_id', 0),
        as_of_date=date.today(),
        pnl_impact=total_pnl,
        pnl_pct=pnl_pct,
        delta_var=delta_var,
        delta_dv01=0.0,  # Would calculate from shocked positions
        delta_duration=0.0,
    )
