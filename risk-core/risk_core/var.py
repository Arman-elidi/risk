"""
VaR calculations: Historical VaR, Stressed VaR
"""
from typing import List
import numpy as np

from .models import VaRMetrics


def calc_historical_var_1d_95(
    pnl_series: List[float],
    window_days: int = 250,
) -> float:
    """
    Calculate 1-day Historical VaR at 95% confidence
    
    Args:
        pnl_series: Daily P&L history (most recent last)
        window_days: Historical window (default 250 trading days = 1 year)
    
    Returns:
        VaR as positive number (potential loss)
    """
    if len(pnl_series) < window_days:
        # Insufficient data, use all available
        data = pnl_series
    else:
        # Use last window_days
        data = pnl_series[-window_days:]
    
    if not data:
        return 0.0
    
    # Sort from worst to best
    sorted_pnl = sorted(data)
    
    # 5th percentile (95% confidence)
    index = int(0.05 * len(sorted_pnl))
    var_value = abs(sorted_pnl[index])
    
    return var_value


def calc_stressed_var(
    pnl_series: List[float],
    stress_start_idx: int,
    stress_end_idx: int,
    confidence: float = 0.95,
) -> float:
    """
    Calculate Stressed VaR using a specific historical stress period
    
    Args:
        pnl_series: Full P&L history
        stress_start_idx: Start index of stress window
        stress_end_idx: End index of stress window
        confidence: Confidence level (default 0.95)
    
    Returns:
        Stressed VaR as positive number
    """
    stress_window = pnl_series[stress_start_idx:stress_end_idx]
    
    if not stress_window:
        return 0.0
    
    sorted_pnl = sorted(stress_window)
    percentile_idx = int((1 - confidence) * len(sorted_pnl))
    stressed_var = abs(sorted_pnl[percentile_idx])
    
    return stressed_var


def calc_var_10d_99(pnl_1d: List[float]) -> float:
    """
    Calculate 10-day VaR at 99% confidence
    Simplified: 10d VaR = 1d VaR × sqrt(10)
    """
    var_1d_99 = calc_historical_var_1d_95(pnl_1d, window_days=250)
    # Adjust to 99% (rough approximation)
    var_1d_99 = var_1d_99 * 1.3  # Rough scaling
    var_10d_99 = var_1d_99 * np.sqrt(10)
    return var_10d_99


def calc_var_metrics(
    pnl_series: List[float],
    stress_window_start: int = 0,
    stress_window_end: int = 60,
) -> VaRMetrics:
    """
    Calculate VaR metrics package
    
    Args:
        pnl_series: Daily P&L history
        stress_window_start: Start of stress period (e.g., COVID March 2020)
        stress_window_end: End of stress period
    
    Returns:
        VaRMetrics object with var_1d_95, stressed_var, var_10d_99
    """
    var_1d = calc_historical_var_1d_95(pnl_series)
    stressed = calc_stressed_var(pnl_series, stress_window_start, stress_window_end)
    var_10d = calc_var_10d_99(pnl_series)
    
    return VaRMetrics(
        var_1d_95=var_1d,
        stressed_var=stressed,
        var_10d_99=var_10d,
    )
