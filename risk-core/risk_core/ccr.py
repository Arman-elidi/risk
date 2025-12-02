"""
Counterparty Credit Risk (CCR) calculations: CE, PFE, EAD_CCR, CVA
"""
from typing import List
import math
from .models import CCRMetrics, InstrumentType, DerivativePosition
from .credit import get_pd, get_lgd


def calc_current_exposure(mtm: float) -> float:
    """
    Current Exposure = max(MtM, 0)
    """
    return max(mtm, 0.0)


def calc_pfe_addon_fx(
    notional: float,
    days_to_maturity: int,
) -> float:
    """
    PFE add-on for FX forwards/options (simplified)
    PFE = Notional × 1% × sqrt(T/250)
    """
    if days_to_maturity <= 0:
        return 0.0
    
    years_fraction = days_to_maturity / 250.0
    addon = notional * 0.01 * math.sqrt(years_fraction)
    return addon


def calc_pfe_addon_ir(
    notional: float,
    days_to_maturity: int,
) -> float:
    """
    PFE add-on for IR swaps (simplified)
    PFE = Notional × 0.5% × sqrt(T/250)
    """
    if days_to_maturity <= 0:
        return 0.0
    
    years_fraction = days_to_maturity / 250.0
    addon = notional * 0.005 * math.sqrt(years_fraction)
    return addon


def calc_ead_ccr(
    current_exposure: float,
    pfe_addon: float,
    wwr_alpha: float = 1.0,
) -> float:
    """
    EAD_CCR = (CE + PFE_addon) × WWR_alpha
    
    Args:
        current_exposure: Current exposure
        pfe_addon: Potential Future Exposure add-on
        wwr_alpha: Wrong-Way Risk multiplier (1.0 - 1.5)
    """
    return (current_exposure + pfe_addon) * wwr_alpha


def calc_ccr_for_counterparty(
    counterparty_id: int,
    derivatives: List[DerivativePosition],
    wwr_alpha: float = 1.0,
    as_of_date = None,
) -> CCRMetrics:
    """
    Calculate CCR metrics for a single counterparty
    
    Args:
        counterparty_id: Counterparty ID
        derivatives: List of derivative positions with this counterparty
        wwr_alpha: Wrong-Way Risk multiplier
        as_of_date: Calculation date
    
    Returns:
        CCRMetrics
    """
    from datetime import date
    if as_of_date is None:
        as_of_date = date.today()
    
    # Aggregate MtM
    total_mtm = sum(d.mtm for d in derivatives)
    ce = calc_current_exposure(total_mtm)
    
    # Calculate PFE add-ons
    total_pfe_addon = 0.0
    peak_pfe = 0.0
    
    for deriv in derivatives:
        days_to_mat = (deriv.maturity_date - as_of_date).days
        
        if deriv.instrument_type in (InstrumentType.FX_FORWARD, InstrumentType.FX_OPTION):
            addon = calc_pfe_addon_fx(abs(deriv.notional), days_to_mat)
        elif deriv.instrument_type in (
            InstrumentType.IR_SWAP,
            InstrumentType.IR_CAP,
            InstrumentType.IR_FLOOR,
            InstrumentType.SWAPTION,
        ):
            addon = calc_pfe_addon_ir(abs(deriv.notional), days_to_mat)
        else:
            addon = 0.0
        
        total_pfe_addon += addon
        peak_pfe = max(peak_pfe, addon)
    
    ead = calc_ead_ccr(ce, total_pfe_addon, wwr_alpha)
    
    return CCRMetrics(
        counterparty_id=counterparty_id,
        current_exposure=ce,
        pfe_current=total_pfe_addon,
        pfe_peak=peak_pfe,
        ead_ccr=ead,
        wwr_alpha=wwr_alpha,
    )


def calc_cva(
    ccr_metrics: CCRMetrics,
    counterparty_rating: str,
    lgd: float = None,
) -> float:
    """
    Calculate CVA (Credit Valuation Adjustment) - simplified
    
    CVA = LGD × PD × EAD_CCR
    
    Args:
        ccr_metrics: CCR metrics for the counterparty
        counterparty_rating: Credit rating
        lgd: Loss Given Default (if None, use default from rating)
    
    Returns:
        CVA value
    """
    pd = get_pd(counterparty_rating)
    if lgd is None:
        lgd = get_lgd("SENIOR")
    
    cva = lgd * pd * ccr_metrics.ead_ccr
    return cva
