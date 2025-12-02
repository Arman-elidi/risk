"""
Credit risk calculations: PD, LGD, EAD, Expected Loss
"""
from typing import List, Dict
from .models import CreditMetrics


# Default PD mapping by rating (simplified)
PD_BY_RATING = {
    "AAA": 0.0001,
    "AA+": 0.0002,
    "AA": 0.0003,
    "AA-": 0.0005,
    "A+": 0.0010,
    "A": 0.0015,
    "A-": 0.0025,
    "BBB+": 0.0050,
    "BBB": 0.0075,
    "BBB-": 0.0120,
    "BB+": 0.0200,
    "BB": 0.0350,
    "BB-": 0.0600,
    "B+": 0.1000,
    "B": 0.1500,
    "B-": 0.2500,
    "CCC+": 0.3500,
    "CCC": 0.5000,
    "CCC-": 0.6500,
    "CC": 0.8000,
    "C": 0.9000,
    "D": 1.0000,
}

# Default LGD by seniority (simplified)
LGD_BY_SENIORITY = {
    "SENIOR_SECURED": 0.25,
    "SENIOR_UNSECURED": 0.40,
    "SENIOR": 0.40,
    "SUBORDINATED": 0.60,
    "JUNIOR": 0.75,
}


def get_pd(rating: str) -> float:
    """Get probability of default by rating"""
    return PD_BY_RATING.get(rating.upper(), 0.01)  # Default 1%


def get_lgd(seniority: str) -> float:
    """Get loss given default by seniority"""
    return LGD_BY_SENIORITY.get(seniority.upper(), 0.45)  # Default 45%


def calc_expected_loss(
    ead: float,
    pd: float,
    lgd: float,
) -> float:
    """
    Calculate expected loss
    EL = EAD × PD × LGD
    """
    return ead * pd * lgd


def calc_portfolio_credit_metrics(
    exposures: List[Dict],
) -> CreditMetrics:
    """
    Calculate portfolio-level credit metrics
    
    Args:
        exposures: List of dicts with keys:
            - exposure (float): EAD
            - rating (str): Credit rating
            - seniority (str): Seniority
    
    Returns:
        CreditMetrics
    """
    if not exposures:
        return CreditMetrics(
            total_exposure=0.0,
            expected_loss=0.0,
            credit_var=0.0,
            pd=0.0,
            lgd=0.0,
            ead=0.0,
        )
    
    total_exposure = sum(e["exposure"] for e in exposures)
    
    total_el = 0.0
    weighted_pd = 0.0
    weighted_lgd = 0.0
    
    for exp in exposures:
        ead = exp["exposure"]
        rating = exp.get("rating", "BBB")
        seniority = exp.get("seniority", "SENIOR")
        
        pd = get_pd(rating)
        lgd = get_lgd(seniority)
        el = calc_expected_loss(ead, pd, lgd)
        
        total_el += el
        if total_exposure > 0:
            weighted_pd += pd * (ead / total_exposure)
            weighted_lgd += lgd * (ead / total_exposure)
    
    # Simplified credit VaR (99% confidence, assuming normal distribution)
    # Credit VaR ≈ EL + 2.33 × sqrt(EL × (1 - PD avg))
    if weighted_pd < 1.0:
        credit_var = total_el + 2.33 * (total_el * (1 - weighted_pd)) ** 0.5
    else:
        credit_var = total_el
    
    return CreditMetrics(
        total_exposure=total_exposure,
        expected_loss=total_el,
        credit_var=credit_var,
        pd=weighted_pd,
        lgd=weighted_lgd,
        ead=total_exposure,
    )
