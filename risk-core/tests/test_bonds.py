"""
Golden Standard Test: Bond Portfolio Metrics
Tests using sample portfolio (KAZAKS30, NAVOI, UZB bonds)
"""
import pytest
from datetime import date
from risk_core.models import BondPosition, DayCountConvention
from risk_core.bonds import (
    calc_bond_metrics,
    calc_portfolio_bond_metrics,
)


@pytest.fixture
def sample_bonds():
    """Sample bond portfolio - Kazakhstan, Navoi, Uzbekistan bonds"""
    as_of = date(2025, 12, 1)
    
    bonds = [
        BondPosition(
            isin="XS2010028593",
            nominal=1000.0,
            quantity=100,  # 100k nominal
            coupon=0.05,  # 5%
            coupon_frequency=2,  # Semi-annual
            maturity_date=date(2030, 7, 21),
            issue_date=date(2019, 7, 21),
            clean_price=98.5,
            ytm=0.052,
            currency="USD",
            seniority="SENIOR",
            rating="BBB-",
        ),
        BondPosition(
            isin="XS2243048671",
            nominal=1000.0,
            quantity=50,  # 50k nominal
            coupon=0.08,  # 8%
            coupon_frequency=2,
            maturity_date=date(2027, 11, 4),
            issue_date=date(2020, 11, 4),
            clean_price=102.0,
            ytm=0.075,
            currency="USD",
            seniority="SENIOR",
            rating="B+",
        ),
        BondPosition(
            isin="XS2686115544",
            nominal=1000.0,
            quantity=75,  # 75k nominal
            coupon=0.07,  # 7%
            coupon_frequency=2,
            maturity_date=date(2029, 10, 20),
            issue_date=date(2023, 10, 20),
            clean_price=99.0,
            ytm=0.0715,
            currency="USD",
            seniority="SENIOR",
            rating="BB-",
        ),
    ]
    
    return bonds, as_of


def test_individual_bond_dv01(sample_bonds):
    """Test DV01 calculation for individual bonds"""
    bonds, as_of = sample_bonds
    
    # Test first bond (Kazakhstan)
    bond1 = bonds[0]
    metrics1 = calc_bond_metrics(bond1, as_of)
    
    # Market value = 98.5% × 100k = 98,500
    expected_mv = 98_500.0
    assert abs(metrics1.market_value - expected_mv) < 100
    
    # DV01 should be positive
    assert metrics1.dv01 > 0
    assert metrics1.modified_duration > 0
    assert metrics1.macaulay_duration > metrics1.modified_duration


def test_portfolio_total_dv01(sample_bonds):
    """Test portfolio total DV01 - должен быть примерно 5,498 USD"""
    bonds, as_of = sample_bonds
    
    portfolio_metrics = calc_portfolio_bond_metrics(bonds, as_of)
    
    # Total DV01 должен быть около 5,498 (из ТЗ golden example)
    expected_dv01 = 5_498.0
    assert abs(portfolio_metrics.total_dv01 - expected_dv01) < 500  # ±500 tolerance
    
    # Total market value
    # Bond1: 98.5 × 100 = 98,500
    # Bond2: 102.0 × 50 = 51,000
    # Bond3: 99.0 × 75 = 74,250
    # Total ≈ 223,750
    expected_mv = 223_750.0
    assert abs(portfolio_metrics.total_market_value - expected_mv) < 1000
    
    # Weighted average duration should be 3-6 years
    assert 3.0 < portfolio_metrics.weighted_avg_duration < 6.0


def test_portfolio_convexity(sample_bonds):
    """Test portfolio convexity"""
    bonds, as_of = sample_bonds
    
    portfolio_metrics = calc_portfolio_bond_metrics(bonds, as_of)
    
    # Convexity should be positive for bond portfolios
    assert portfolio_metrics.convexity > 0


def test_empty_portfolio():
    """Test edge case: empty portfolio"""
    portfolio_metrics = calc_portfolio_bond_metrics([], date(2025, 12, 1))
    
    assert portfolio_metrics.total_market_value == 0.0
    assert portfolio_metrics.total_dv01 == 0.0
    assert portfolio_metrics.weighted_avg_duration == 0.0
