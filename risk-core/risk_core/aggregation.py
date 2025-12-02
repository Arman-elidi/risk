"""
Portfolio risk aggregation - main orchestrator
Combines all risk modules into single PortfolioRiskResult
"""
from datetime import date
from typing import List, Dict, Optional
import time

from .models import (
    BondPosition,
    DerivativePosition,
    PortfolioRiskResult,
    PortfolioBondMetrics,
    VaRMetrics,
    CreditMetrics,
    CCRMetrics,
    LiquidityMetrics,
    CapitalMetrics,
)
from . import bonds, var, credit, ccr, liquidity, capital, derivatives


def aggregate_portfolio_risks(
    portfolio_id: int,
    as_of_date: date,
    bond_positions: List[BondPosition],
    derivative_positions: List[DerivativePosition],
    pnl_history: List[float],
    # Market data
    spot_prices: Dict[str, float] = None,
    vol_surfaces: Dict[str, float] = None,
    # Credit data
    credit_exposures: List[Dict] = None,
    counterparty_derivatives: Dict[int, List[DerivativePosition]] = None,
    counterparty_ratings: Dict[int, str] = None,
    # Liquidity data
    liquidity_positions: List[Dict] = None,
    hqla: float = 0.0,
    net_cash_outflows_30d: float = 0.0,
    assets_by_bucket: Dict[str, float] = None,
    liabilities_by_bucket: Dict[str, float] = None,
    # Capital data
    aum_avg: float = 0.0,
    client_money_held_avg: float = 0.0,
    client_orders_volume_avg: float = 0.0,
    own_funds: float = 0.0,
    # WWR
    wwr_alpha: float = 1.0,
    engine_version: str = "0.1.0",
) -> PortfolioRiskResult:
    """
    Main aggregation function - calculates all risk metrics
    
    This is the entry point called by risk-service to compute portfolio risks.
    
    Args:
        portfolio_id: Portfolio identifier
        as_of_date: Calculation date
        bond_positions: List of bond positions
        derivative_positions: List of derivative positions
        pnl_history: Historical P&L series for VaR
        spot_prices: Spot prices for derivatives (underlying -> price)
        vol_surfaces: Implied vols (underlying -> vol)
        credit_exposures: Credit exposure data
        counterparty_derivatives: Derivatives grouped by counterparty
        counterparty_ratings: Counterparty ratings
        liquidity_positions: Positions for liquidity calcs
        hqla: High Quality Liquid Assets
        net_cash_outflows_30d: Net cash outflows
        assets_by_bucket: Assets by maturity bucket
        liabilities_by_bucket: Liabilities by maturity bucket
        aum_avg: Average AUM
        client_money_held_avg: Client money
        client_orders_volume_avg: Client orders volume
        own_funds: Own funds
        wwr_alpha: Wrong-Way Risk multiplier
        engine_version: Version tag
    
    Returns:
        PortfolioRiskResult with all metrics
    """
    start_time = time.time()
    
    # Defaults
    spot_prices = spot_prices or {}
    vol_surfaces = vol_surfaces or {}
    credit_exposures = credit_exposures or []
    counterparty_derivatives = counterparty_derivatives or {}
    counterparty_ratings = counterparty_ratings or {}
    liquidity_positions = liquidity_positions or []
    assets_by_bucket = assets_by_bucket or {}
    liabilities_by_bucket = liabilities_by_bucket or {}
    
    # 1. Bond metrics
    bond_metrics = None
    if bond_positions:
        bond_metrics = bonds.calc_portfolio_bond_metrics(bond_positions, as_of_date)
    
    # 2. VaR metrics
    var_metrics = None
    if pnl_history:
        var_metrics = var.calc_var_metrics(pnl_history)
    
    # 3. Credit metrics
    credit_metrics_result = None
    if credit_exposures:
        credit_metrics_result = credit.calc_portfolio_credit_metrics(credit_exposures)
    
    # 4. CCR metrics (per counterparty)
    ccr_metrics_list = []
    cva_total = 0.0
    
    for cpty_id, derivs in counterparty_derivatives.items():
        if not derivs:
            continue
        
        ccr_m = ccr.calc_ccr_for_counterparty(
            cpty_id,
            derivs,
            wwr_alpha=wwr_alpha,
            as_of_date=as_of_date,
        )
        ccr_metrics_list.append(ccr_m)
        
        # CVA
        cpty_rating = counterparty_ratings.get(cpty_id, "BBB")
        cva_value = ccr.calc_cva(ccr_m, cpty_rating)
        cva_total += cva_value
    
    # 5. Liquidity metrics
    liq_metrics = None
    if liquidity_positions:
        liq_metrics = liquidity.calc_liquidity_metrics(
            liquidity_positions,
            hqla,
            net_cash_outflows_30d,
            assets_by_bucket,
            liabilities_by_bucket,
        )
    
    # 6. Capital metrics
    var_1d_95 = var_metrics.var_1d_95 if var_metrics else 0.0
    
    cap_metrics = capital.calc_capital_metrics(
        var_1d_95=var_1d_95,
        aum_avg=aum_avg,
        client_money_held_avg=client_money_held_avg,
        client_orders_volume_avg=client_orders_volume_avg,
        own_funds=own_funds,
    )
    
    # 7. Derivatives Greeks (optional, not in core result but can be added)
    # greeks = derivatives.calc_portfolio_greeks(
    #     derivative_positions, spot_prices, vol_surfaces
    # )
    
    calc_time = time.time() - start_time
    
    return PortfolioRiskResult(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        engine_version=engine_version,
        bond_metrics=bond_metrics,
        var_metrics=var_metrics,
        credit_metrics=credit_metrics_result,
        ccr_metrics=ccr_metrics_list if ccr_metrics_list else None,
        liquidity_metrics=liq_metrics,
        capital_metrics=cap_metrics,
        calculation_time_seconds=calc_time,
    )
