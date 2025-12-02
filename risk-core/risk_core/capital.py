"""
Capital adequacy calculations: IFR K-factors, capital ratio
"""
from .models import CapitalMetrics


def calc_k_npr(
    var_1d_95: float,
    multiplier: float = 3.0,
) -> float:
    """
    Calculate K-NPR (Net Position Risk)
    
    Simplified: K-NPR = VaR × multiplier
    (In practice, use standardized approach or VaR-based approach per IFR)
    
    Args:
        var_1d_95: 1-day VaR at 95% confidence
        multiplier: Regulatory multiplier (typically 3.0)
    
    Returns:
        K-NPR capital requirement
    """
    return var_1d_95 * multiplier


def calc_k_aum(
    aum_avg: float,
    rate: float = 0.0002,
) -> float:
    """
    Calculate K-AUM (Assets Under Management)
    
    K-AUM = 0.02% × AUM_avg
    
    Args:
        aum_avg: Average AUM over period
        rate: Rate (0.02% = 0.0002)
    
    Returns:
        K-AUM capital requirement
    """
    return aum_avg * rate


def calc_k_cmh(
    client_money_held_avg: float,
    rate: float = 0.004,
) -> float:
    """
    Calculate K-CMH (Client Money Held)
    
    K-CMH based on average client funds
    
    Args:
        client_money_held_avg: Average client money held
        rate: Rate (simplified, adjust per IFR guidance)
    
    Returns:
        K-CMH capital requirement
    """
    return client_money_held_avg * rate


def calc_k_coh(
    client_orders_volume_avg: float,
    rate: float = 0.001,
) -> float:
    """
    Calculate K-COH (Client Orders Handled)
    
    K-COH based on client order flow volume
    
    Args:
        client_orders_volume_avg: Average daily client orders volume
        rate: Rate (simplified)
    
    Returns:
        K-COH capital requirement
    """
    return client_orders_volume_avg * rate


def calc_capital_metrics(
    var_1d_95: float = 0.0,
    aum_avg: float = 0.0,
    client_money_held_avg: float = 0.0,
    client_orders_volume_avg: float = 0.0,
    own_funds: float = 0.0,
    k_npr_multiplier: float = 3.0,
) -> CapitalMetrics:
    """
    Calculate complete capital adequacy metrics
    
    Args:
        var_1d_95: 1-day VaR at 95%
        aum_avg: Average AUM
        client_money_held_avg: Average client money
        client_orders_volume_avg: Average client orders volume
        own_funds: Own funds (equity)
        k_npr_multiplier: Multiplier for K-NPR
    
    Returns:
        CapitalMetrics
    """
    k_npr = calc_k_npr(var_1d_95, k_npr_multiplier)
    k_aum = calc_k_aum(aum_avg)
    k_cmh = calc_k_cmh(client_money_held_avg)
    k_coh = calc_k_coh(client_orders_volume_avg)
    
    total_k_req = k_npr + k_aum + k_cmh + k_coh
    
    if total_k_req > 0:
        capital_ratio = own_funds / total_k_req
    else:
        capital_ratio = 999.9  # No requirements = infinite ratio
    
    return CapitalMetrics(
        k_npr=k_npr,
        k_aum=k_aum,
        k_cmh=k_cmh,
        k_coh=k_coh,
        total_k_req=total_k_req,
        own_funds=own_funds,
        capital_ratio=capital_ratio,
    )
