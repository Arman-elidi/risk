"""
Bond risk calculations: DV01, duration, convexity, WAM, WAR
"""
from datetime import date
from typing import List, Tuple
import numpy as np

from .models import (
    BondPosition,
    BondMetrics,
    PortfolioBondMetrics,
    DayCountConvention,
)


def year_fraction(start: date, end: date, convention: DayCountConvention) -> float:
    """Calculate year fraction between two dates"""
    days = (end - start).days
    
    if convention == DayCountConvention.ACT_365:
        return days / 365.0
    elif convention == DayCountConvention.ACT_360:
        return days / 360.0
    elif convention == DayCountConvention.ACT_ACT:
        # Simplified ACT/ACT
        return days / 365.25
    elif convention in (DayCountConvention.THIRTY_360, DayCountConvention.THIRTY_E_360):
        # Simplified 30/360
        y1, m1, d1 = start.year, start.month, start.day
        y2, m2, d2 = end.year, end.month, end.day
        return ((y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)) / 360.0
    
    return days / 365.0


def generate_cashflows(
    bond: BondPosition,
    as_of_date: date,
) -> List[Tuple[date, float, float]]:
    """
    Generate bond cashflows from as_of_date to maturity
    Returns: list of (payment_date, coupon_payment, year_fraction)
    """
    cashflows = []
    annual_coupon = bond.coupon * bond.nominal
    coupon_payment = annual_coupon / bond.coupon_frequency
    
    # Determine next coupon date
    # Simplified: assume regular intervals from maturity backwards
    from dateutil.relativedelta import relativedelta
    months_interval = 12 // bond.coupon_frequency
    
    current_date = bond.maturity_date
    while current_date > as_of_date:
        yf = year_fraction(as_of_date, current_date, bond.day_count)
        if current_date == bond.maturity_date:
            # Final payment = coupon + principal
            cashflows.append((current_date, coupon_payment + bond.nominal, yf))
        else:
            cashflows.append((current_date, coupon_payment, yf))
        current_date = current_date - relativedelta(months=months_interval)
    
    # Reverse to chronological order
    cashflows.reverse()
    return cashflows


def price_from_yield(
    bond: BondPosition,
    ytm: float,
    as_of_date: date,
) -> float:
    """Calculate clean price from yield to maturity"""
    cashflows = generate_cashflows(bond, as_of_date)
    
    pv = 0.0
    for pay_date, cf, yf in cashflows:
        pv += cf / ((1 + ytm) ** yf)
    
    # Clean price as % of nominal
    clean_price = (pv / bond.nominal) * 100.0
    return clean_price


def calc_macaulay_duration(
    bond: BondPosition,
    ytm: float,
    as_of_date: date,
) -> float:
    """Calculate Macaulay duration"""
    cashflows = generate_cashflows(bond, as_of_date)
    
    pv_total = 0.0
    weighted_time = 0.0
    
    for pay_date, cf, yf in cashflows:
        discount_factor = 1 / ((1 + ytm) ** yf)
        pv = cf * discount_factor
        pv_total += pv
        weighted_time += yf * pv
    
    if pv_total == 0:
        return 0.0
    
    macaulay_duration = weighted_time / pv_total
    return macaulay_duration


def calc_modified_duration(
    bond: BondPosition,
    ytm: float,
    as_of_date: date,
) -> float:
    """Calculate modified duration"""
    mac_dur = calc_macaulay_duration(bond, ytm, as_of_date)
    # Simplified: assuming annual compounding
    mod_dur = mac_dur / (1 + ytm)
    return mod_dur


def calc_convexity(
    bond: BondPosition,
    ytm: float,
    as_of_date: date,
) -> float:
    """Calculate convexity"""
    cashflows = generate_cashflows(bond, as_of_date)
    
    pv_total = 0.0
    convexity_sum = 0.0
    
    for pay_date, cf, yf in cashflows:
        discount_factor = 1 / ((1 + ytm) ** yf)
        pv = cf * discount_factor
        pv_total += pv
        convexity_sum += yf * (yf + 1) * pv
    
    if pv_total == 0:
        return 0.0
    
    convexity = convexity_sum / (pv_total * ((1 + ytm) ** 2))
    return convexity


def calc_dv01(
    bond: BondPosition,
    ytm: float,
    market_value: float,
    as_of_date: date,
) -> float:
    """
    Calculate DV01 (Dollar Value of 1bp)
    DV01 = Modified Duration × Market Value × 0.0001
    """
    mod_dur = calc_modified_duration(bond, ytm, as_of_date)
    dv01 = mod_dur * market_value * 0.0001
    return dv01


def calc_spread_duration(
    bond: BondPosition,
    ytm: float,
    spread_bps: float,
    as_of_date: date,
) -> float:
    """
    Calculate spread duration (sensitivity to credit spread changes)
    According to techspec section 4.3
    
    SD ≈ Modified Duration × (spread / (ytm + spread))
    """
    mod_dur = calc_modified_duration(bond, ytm, as_of_date)
    
    spread_decimal = spread_bps / 10000.0
    total_yield = ytm + spread_decimal
    
    if total_yield == 0:
        return 0.0
    
    spread_duration = mod_dur * (spread_decimal / total_yield)
    return spread_duration


def calc_accrued_interest(
    bond: BondPosition,
    as_of_date: date,
) -> float:
    """Calculate accrued interest since last coupon"""
    # Simplified: assume we're between coupons
    # Find previous coupon date
    from dateutil.relativedelta import relativedelta
    months_interval = 12 // bond.coupon_frequency
    
    # Work backwards from maturity
    last_coupon_date = bond.maturity_date
    while last_coupon_date > as_of_date:
        last_coupon_date = last_coupon_date - relativedelta(months=months_interval)
    
    next_coupon_date = last_coupon_date + relativedelta(months=months_interval)
    
    days_accrued = (as_of_date - last_coupon_date).days
    days_in_period = (next_coupon_date - last_coupon_date).days
    
    if days_in_period == 0:
        return 0.0
    
    annual_coupon = bond.coupon * bond.nominal
    coupon_payment = annual_coupon / bond.coupon_frequency
    accrued = coupon_payment * (days_accrued / days_in_period)
    
    return accrued


def calc_bond_metrics(
    bond: BondPosition,
    as_of_date: date,
) -> BondMetrics:
    """Calculate all risk metrics for a single bond position"""
    # Market value
    market_value = (bond.clean_price / 100.0) * bond.nominal * bond.quantity
    
    # Duration, DV01, Convexity
    mod_dur = calc_modified_duration(bond, bond.ytm, as_of_date)
    mac_dur = calc_macaulay_duration(bond, bond.ytm, as_of_date)
    convexity = calc_convexity(bond, bond.ytm, as_of_date)
    dv01 = calc_dv01(bond, bond.ytm, market_value, as_of_date)
    accrued = calc_accrued_interest(bond, as_of_date)
    
    return BondMetrics(
        position_id=bond.isin,
        dv01=dv01,
        modified_duration=mod_dur,
        macaulay_duration=mac_dur,
        convexity=convexity,
        market_value=market_value,
        accrued_interest=accrued,
    )


def calc_portfolio_bond_metrics(
    bonds: List[BondPosition],
    as_of_date: date,
) -> PortfolioBondMetrics:
    """Calculate aggregated bond portfolio metrics"""
    if not bonds:
        return PortfolioBondMetrics(
            total_market_value=0.0,
            total_dv01=0.0,
            weighted_avg_duration=0.0,
            weighted_avg_maturity=0.0,
            convexity=0.0,
        )
    
    metrics = [calc_bond_metrics(b, as_of_date) for b in bonds]
    
    total_mv = sum(m.market_value for m in metrics)
    total_dv01 = sum(m.dv01 for m in metrics)
    
    if total_mv > 0:
        weighted_duration = sum(
            m.modified_duration * m.market_value for m in metrics
        ) / total_mv
        
        weighted_convexity = sum(
            m.convexity * m.market_value for m in metrics
        ) / total_mv
    else:
        weighted_duration = 0.0
        weighted_convexity = 0.0
    
    # WAM - Weighted Average Maturity (in years)
    if total_mv > 0:
        wam = sum(
            year_fraction(as_of_date, b.maturity_date, b.day_count) * (b.clean_price / 100.0 * b.nominal * b.quantity)
            for b in bonds
        ) / total_mv
    else:
        wam = 0.0
    
    return PortfolioBondMetrics(
        total_market_value=total_mv,
        total_dv01=total_dv01,
        weighted_avg_duration=weighted_duration,
        weighted_avg_maturity=wam,
        convexity=weighted_convexity,
    )
