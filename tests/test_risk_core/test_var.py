"""
Unit tests for VaR calculations
"""
import pytest
import numpy as np
from risk_core import var as var_module


@pytest.mark.unit
class TestVaRCalculations:
    """Test VaR calculations"""
    
    def test_calc_historical_var(self):
        """Test historical VaR calculation"""
        # Generate sample P&L history (250 days)
        np.random.seed(42)
        pnl_history = np.random.normal(1000, 5000, 250).tolist()
        
        confidence_level = 0.95
        
        var = var_module.calc_historical_var(pnl_history, confidence_level)
        
        # VaR should be negative (loss)
        assert var < 0
        # Should be reasonable magnitude
        assert -20000 < var < 0
    
    def test_calc_var_metrics(self):
        """Test complete VaR metrics calculation"""
        # Generate sample P&L
        np.random.seed(42)
        pnl_history = np.random.normal(1000, 5000, 250).tolist()
        
        metrics = var_module.calc_var_metrics(pnl_history)
        
        # Check all metrics calculated
        assert metrics.var_1d_95 < 0
        assert metrics.var_1d_99 < 0
        assert metrics.var_10d_95 < 0
        
        # VaR 99% should be worse than 95%
        assert metrics.var_1d_99 < metrics.var_1d_95
        
        # 10-day VaR should be worse than 1-day
        assert abs(metrics.var_10d_95) > abs(metrics.var_1d_95)
    
    def test_calc_stressed_var(self):
        """Test stressed VaR calculation"""
        np.random.seed(42)
        
        # Normal period
        pnl_history = np.random.normal(1000, 5000, 250).tolist()
        
        # Stress period (higher volatility)
        stressed_pnl = np.random.normal(-2000, 10000, 60).tolist()
        
        stressed_var = var_module.calc_stressed_var(stressed_pnl, 0.95)
        normal_var = var_module.calc_historical_var(pnl_history, 0.95)
        
        # Stressed VaR should be worse
        assert stressed_var < normal_var
        assert stressed_var < -5000  # Significant stress
    
    def test_insufficient_data(self):
        """Test VaR with insufficient data"""
        pnl_history = [100, -200, 300]  # Only 3 points
        
        with pytest.raises(ValueError):
            var_module.calc_historical_var(pnl_history, 0.95)
    
    def test_extreme_confidence_levels(self):
        """Test VaR with extreme confidence levels"""
        np.random.seed(42)
        pnl_history = np.random.normal(1000, 5000, 250).tolist()
        
        # Very high confidence (99.9%)
        var_999 = var_module.calc_historical_var(pnl_history, 0.999)
        var_95 = var_module.calc_historical_var(pnl_history, 0.95)
        
        # Higher confidence should give worse VaR
        assert var_999 < var_95
    
    def test_all_positive_pnl(self):
        """Test VaR when all P&L is positive (no losses)"""
        pnl_history = [100, 200, 300, 400, 500] * 50  # All gains
        
        var = var_module.calc_historical_var(pnl_history, 0.95)
        
        # VaR should be positive (no losses in history)
        assert var >= 0
    
    def test_var_backtesting_breaches(self):
        """Test VaR backtesting breach detection"""
        np.random.seed(42)
        
        # Generate P&L and VaR estimates
        actual_pnl = np.random.normal(0, 1000, 100).tolist()
        var_estimates = [-800] * 100  # Fixed VaR estimate
        
        breaches = var_module.count_var_breaches(actual_pnl, var_estimates)
        
        # Should have some breaches (but not too many for 95% confidence)
        assert 0 < breaches < 20  # Roughly 5% of 100 = 5 breaches expected
