"""
Liquidity risk calculations: LCR, funding gaps, liquidation costs
"""
from typing import List, Dict
from .models import LiquidityMetrics


def calc_lcr(
    hqla: float,
    net_cash_outflows_30d: float,
) -> float:
    """
    Calculate Liquidity Coverage Ratio
    
    LCR = HQLA / Net Cash Outflows (30 days)
    
    Requirement: LCR ≥ 100%
    """
    if net_cash_outflows_30d == 0:
        return 999.9  # No outflows = infinite liquidity
    
    lcr = hqla / net_cash_outflows_30d
    return lcr


def calc_funding_gap(
    assets_by_bucket: Dict[str, float],
    liabilities_by_bucket: Dict[str, float],
) -> Dict[str, float]:
    """
    Calculate funding gap by maturity bucket
    
    Gap = Assets - Liabilities
    
    Args:
        assets_by_bucket: {"0-7d": 1M, "7-30d": 2M, ...}
        liabilities_by_bucket: {"0-7d": 1.5M, "7-30d": 1M, ...}
    
    Returns:
        Dict with gaps by bucket
    """
    all_buckets = set(assets_by_bucket.keys()) | set(liabilities_by_bucket.keys())
    gaps = {}
    
    for bucket in all_buckets:
        assets = assets_by_bucket.get(bucket, 0.0)
        liabilities = liabilities_by_bucket.get(bucket, 0.0)
        gaps[bucket] = assets - liabilities
    
    return gaps


def calc_liquidation_cost(
    positions: List[Dict],
    urgency_factor: float = 1.0,
) -> float:
    """
    Calculate liquidation cost for portfolio
    
    LC = Σ (Position_i × BidAskSpread_i × Urgency_Factor)
    
    Args:
        positions: List of dicts with keys:
            - market_value (float)
            - bid_ask_spread_bps (float): bid-ask spread in basis points
        urgency_factor: Multiplier for urgent liquidation (1.0 = normal, 1.5 = urgent)
    
    Returns:
        Total liquidation cost in currency units
    """
    total_cost = 0.0
    
    for pos in positions:
        mv = pos.get("market_value", 0.0)
        spread_bps = pos.get("bid_ask_spread_bps", 10.0)  # Default 10 bps
        
        # Convert bps to fraction
        spread_fraction = spread_bps / 10000.0
        cost = mv * spread_fraction * urgency_factor
        total_cost += cost
    
    return total_cost


def calc_liquidity_score(
    positions: List[Dict],
) -> float:
    """
    Calculate weighted liquidity score for portfolio (0-1 scale)
    
    1.0 = highly liquid (government bonds, FX majors)
    0.0 = illiquid (exotic derivatives, distressed bonds)
    
    Args:
        positions: List with keys:
            - market_value (float)
            - liquidity_score (float): 0-1
    
    Returns:
        Weighted average liquidity score
    """
    total_mv = sum(p.get("market_value", 0.0) for p in positions)
    
    if total_mv == 0:
        return 1.0
    
    weighted_score = sum(
        p.get("market_value", 0.0) * p.get("liquidity_score", 0.5)
        for p in positions
    ) / total_mv
    
    return weighted_score


def calc_liquidity_metrics(
    positions: List[Dict],
    hqla: float,
    net_cash_outflows_30d: float,
    assets_by_bucket: Dict[str, float],
    liabilities_by_bucket: Dict[str, float],
) -> LiquidityMetrics:
    """
    Calculate comprehensive liquidity metrics
    
    Args:
        positions: List of position dicts
        hqla: High Quality Liquid Assets
        net_cash_outflows_30d: Net cash outflows over 30 days
        assets_by_bucket: Assets by maturity bucket
        liabilities_by_bucket: Liabilities by maturity bucket
    
    Returns:
        LiquidityMetrics
    """
    lcr = calc_lcr(hqla, net_cash_outflows_30d)
    
    # Liquidation costs
    lc_1d = calc_liquidation_cost(positions, urgency_factor=1.5)  # Urgent
    lc_5d = calc_liquidation_cost(positions, urgency_factor=1.0)  # Normal
    
    # Liquidity score
    liq_score = calc_liquidity_score(positions)
    
    # Funding gap (short-term bucket)
    gaps = calc_funding_gap(assets_by_bucket, liabilities_by_bucket)
    funding_gap_short = gaps.get("0-7d", 0.0) + gaps.get("7-30d", 0.0)
    
    return LiquidityMetrics(
        liquidation_cost_1d=lc_1d,
        liquidation_cost_5d=lc_5d,
        liquidity_score=liq_score,
        lcr_ratio=lcr,
        funding_gap_short_term=funding_gap_short,
    )
