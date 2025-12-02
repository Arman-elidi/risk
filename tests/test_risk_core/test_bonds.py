"""
Unit tests for bond risk calculations
"""
import pytest
from datetime import date
from risk_core.models import BondPosition
from risk_core import bonds


@pytest.mark.unit
class TestBondCalculations:
    """Test bond risk metric calculations"""
    
    def test_calc_macaulay_duration(self):
        """Test Macaulay duration calculation"""
        bond = BondPosition(
            isin="TEST001",
            notional=1000000.0,
            clean_price=98.5,
            coupon_rate=0.025,
            maturity_date=date(2030, 12, 31),
            issue_date=date(2020, 1, 1),
            coupon_frequency=2,
            issuer_id=1,
        )
        
        ytm = 0.03
        as_of_date = date(2024, 1, 1)
        
        duration = bonds.calc_macaulay_duration(bond, ytm, as_of_date)
        
        # Macaulay duration should be positive and reasonable
        assert duration > 0
        assert duration < 20  # Reasonable for 6-year bond
        assert isinstance(duration, float)
    
    def test_calc_modified_duration(self):
        """Test modified duration calculation"""
        bond = BondPosition(
            isin="TEST001",
            notional=1000000.0,
            clean_price=98.5,
            coupon_rate=0.025,
            maturity_date=date(2030, 12, 31),
            issue_date=date(2020, 1, 1),
            coupon_frequency=2,
            issuer_id=1,
        )
        
        ytm = 0.03
        as_of_date = date(2024, 1, 1)
        
        mod_duration = bonds.calc_modified_duration(bond, ytm, as_of_date)
        mac_duration = bonds.calc_macaulay_duration(bond, ytm, as_of_date)
        
        # Modified duration should be less than Macaulay
        assert mod_duration < mac_duration
        assert mod_duration > 0
    
    def test_calc_dv01(self):
        """Test DV01 calculation"""
        bond = BondPosition(
            isin="TEST001",
            notional=1000000.0,
            clean_price=98.5,
            coupon_rate=0.025,
            maturity_date=date(2030, 12, 31),
            issue_date=date(2020, 1, 1),
            coupon_frequency=2,
            issuer_id=1,
        )
        
        ytm = 0.03
        market_value = 985000.0
        as_of_date = date(2024, 1, 1)
        
        dv01 = bonds.calc_dv01(bond, ytm, market_value, as_of_date)
        
        # DV01 should be positive for long positions
        assert dv01 > 0
        # Should be reasonable magnitude
        assert 100 < dv01 < 10000
    
    def test_calc_convexity(self):
        """Test convexity calculation"""
        bond = BondPosition(
            isin="TEST001",
            notional=1000000.0,
            clean_price=98.5,
            coupon_rate=0.025,
            maturity_date=date(2030, 12, 31),
            issue_date=date(2020, 1, 1),
            coupon_frequency=2,
            issuer_id=1,
        )
        
        ytm = 0.03
        as_of_date = date(2024, 1, 1)
        
        convexity = bonds.calc_convexity(bond, ytm, as_of_date)
        
        # Convexity should be positive
        assert convexity > 0
        # Should be reasonable
        assert convexity < 200
    
    def test_calc_portfolio_bond_metrics(self):
        """Test portfolio-level bond metrics"""
        positions = [
            BondPosition(
                isin="TEST001",
                notional=1000000.0,
                clean_price=98.5,
                coupon_rate=0.025,
                maturity_date=date(2030, 12, 31),
                issue_date=date(2020, 1, 1),
                coupon_frequency=2,
                issuer_id=1,
            ),
            BondPosition(
                isin="TEST002",
                notional=500000.0,
                clean_price=102.0,
                coupon_rate=0.035,
                maturity_date=date(2028, 6, 30),
                issue_date=date(2021, 1, 1),
                coupon_frequency=2,
                issuer_id=2,
            ),
        ]
        
        as_of_date = date(2024, 1, 1)
        
        metrics = bonds.calc_portfolio_bond_metrics(positions, as_of_date)
        
        # Check all metrics are calculated
        assert metrics.dv01_total > 0
        assert metrics.duration > 0
        assert metrics.convexity > 0
        assert metrics.total_market_value > 0
        assert len(metrics.bond_metrics) == 2
    
    def test_generate_cashflows(self):
        """Test cashflow generation"""
        bond = BondPosition(
            isin="TEST001",
            notional=1000000.0,
            clean_price=98.5,
            coupon_rate=0.025,
            maturity_date=date(2026, 12, 31),
            issue_date=date(2024, 1, 1),
            coupon_frequency=2,
            issuer_id=1,
        )
        
        as_of_date = date(2024, 1, 1)
        
        cashflows = bonds.generate_cashflows(bond, as_of_date)
        
        # Should have 6 cashflows (2 per year for 3 years)
        assert len(cashflows) == 6
        
        # Check structure
        for cf in cashflows:
            pay_date, amount, year_fraction = cf
            assert isinstance(pay_date, date)
            assert amount > 0
            assert year_fraction > 0
        
        # Last cashflow should include principal
        last_cf = cashflows[-1]
        assert last_cf[1] > bond.notional * bond.coupon_rate * 0.5  # More than just coupon
    
    def test_zero_coupon_bond(self):
        """Test zero-coupon bond calculations"""
        bond = BondPosition(
            isin="ZERO001",
            notional=1000000.0,
            clean_price=85.0,
            coupon_rate=0.0,  # Zero coupon
            maturity_date=date(2029, 12, 31),
            issue_date=date(2024, 1, 1),
            coupon_frequency=0,
            issuer_id=1,
        )
        
        ytm = 0.035
        as_of_date = date(2024, 1, 1)
        
        duration = bonds.calc_macaulay_duration(bond, ytm, as_of_date)
        
        # For zero-coupon, Macaulay duration ≈ time to maturity
        years_to_maturity = (bond.maturity_date - as_of_date).days / 365.25
        assert abs(duration - years_to_maturity) < 0.5  # Within 6 months
