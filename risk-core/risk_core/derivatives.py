"""
Derivatives calculations: Greeks, pricing (simplified)
"""
from typing import List, Dict
import math
from .models import DerivativePosition, InstrumentType


def black_scholes_call(
    S: float,  # Spot price
    K: float,  # Strike
    T: float,  # Time to maturity (years)
    r: float,  # Risk-free rate
    sigma: float,  # Volatility
) -> float:
    """Black-Scholes call option price"""
    if T <= 0:
        return max(S - K, 0)
    
    from scipy.stats import norm
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return call_price


def black_scholes_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Black-Scholes put option price"""
    if T <= 0:
        return max(K - S, 0)
    
    from scipy.stats import norm
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    put_price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return put_price


def calc_option_delta(
    option_type: str,  # CALL or PUT
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Calculate option delta"""
    if T <= 0:
        if option_type.upper() == "CALL":
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0
    
    from scipy.stats import norm
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    
    if option_type.upper() == "CALL":
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1.0


def calc_option_gamma(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Calculate option gamma (same for call and put)"""
    if T <= 0:
        return 0.0
    
    from scipy.stats import norm
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
    return gamma


def calc_option_vega(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Calculate option vega (same for call and put)"""
    if T <= 0:
        return 0.0
    
    from scipy.stats import norm
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    vega = S * norm.pdf(d1) * math.sqrt(T)
    return vega / 100.0  # Per 1% vol change


def calc_option_theta(
    option_type: str,
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Calculate option theta (time decay)"""
    if T <= 0:
        return 0.0
    
    from scipy.stats import norm
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    if option_type.upper() == "CALL":
        theta = (
            -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))
            - r * K * math.exp(-r * T) * norm.cdf(d2)
        )
    else:
        theta = (
            -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))
            + r * K * math.exp(-r * T) * norm.cdf(-d2)
        )
    
    return theta / 365.0  # Per day


def calc_portfolio_greeks(
    derivatives: List[DerivativePosition],
    spot_prices: Dict[str, float],
    vol_surfaces: Dict[str, float],
    risk_free_rate: float = 0.03,
) -> Dict[str, float]:
    """
    Calculate aggregated Greeks for derivatives portfolio
    
    Args:
        derivatives: List of derivative positions
        spot_prices: Dict mapping underlying -> spot price
        vol_surfaces: Dict mapping underlying -> implied vol
        risk_free_rate: Risk-free rate
    
    Returns:
        Dict with total delta, gamma, vega, theta
    """
    total_delta = 0.0
    total_gamma = 0.0
    total_vega = 0.0
    total_theta = 0.0
    
    from datetime import date
    
    for deriv in derivatives:
        if deriv.instrument_type not in (InstrumentType.FX_OPTION, InstrumentType.SWAPTION):
            continue
        
        S = spot_prices.get(deriv.underlying, 100.0)
        K = deriv.strike or 100.0
        sigma = vol_surfaces.get(deriv.underlying, 0.20)
        
        days_to_mat = (deriv.maturity_date - date.today()).days
        T = max(days_to_mat / 365.0, 0.0)
        
        option_type = deriv.option_type or "CALL"
        
        # Calculate Greeks
        delta = calc_option_delta(option_type, S, K, T, risk_free_rate, sigma)
        gamma = calc_option_gamma(S, K, T, risk_free_rate, sigma)
        vega = calc_option_vega(S, K, T, risk_free_rate, sigma)
        theta = calc_option_theta(option_type, S, K, T, risk_free_rate, sigma)
        
        # Scale by notional and quantity
        notional_scaled = deriv.notional
        
        total_delta += delta * notional_scaled
        total_gamma += gamma * notional_scaled
        total_vega += vega * notional_scaled
        total_theta += theta * notional_scaled
    
    return {
        "delta": total_delta,
        "gamma": total_gamma,
        "vega": total_vega,
        "theta": total_theta,
    }
