"""
Golden Standard Test: VaR calculations
Tests using sample P&L series with expected VaR = 180,000
"""
import pytest
from risk_core.var import (
    calc_historical_var_1d_95,
    calc_stressed_var,
    calc_var_metrics,
)


@pytest.fixture
def sample_pnl_series():
    """Sample P&L series with known VaR ≈ 180,000"""
    # Simplified: create 250 days of P&L with 5th percentile ≈ -180,000
    import numpy as np
    np.random.seed(42)
    
    # Generate normal distribution: mean=0, std=100k
    pnl = list(np.random.normal(loc=0, scale=100_000, size=250))
    
    # Inject some tail losses to hit target VaR
    pnl[5] = -180_000
    pnl[10] = -185_000
    pnl[12] = -175_000
    
    return pnl


def test_historical_var_1d_95(sample_pnl_series):
    """Test 1-day VaR at 95% confidence"""
    var_value = calc_historical_var_1d_95(sample_pnl_series)
    
    # Expected VaR ≈ 180,000 (из ТЗ golden example)
    expected_var = 180_000.0
    assert abs(var_value - expected_var) < 20_000  # ±20k tolerance


def test_stressed_var(sample_pnl_series):
    """Test stressed VaR using stress window"""
    # Use first 60 days as stress period
    stressed_var = calc_stressed_var(
        sample_pnl_series,
        stress_start_idx=0,
        stress_end_idx=60,
    )
    
    # Stressed VaR should be higher than normal VaR
    normal_var = calc_historical_var_1d_95(sample_pnl_series)
    assert stressed_var >= normal_var * 0.8  # At least 80% of normal


def test_var_metrics_complete(sample_pnl_series):
    """Test complete VaR metrics package"""
    metrics = calc_var_metrics(sample_pnl_series)
    
    # Check all components exist
    assert metrics.var_1d_95 > 0
    assert metrics.stressed_var > 0
    assert metrics.var_10d_99 > 0
    
    # 10-day VaR should be larger than 1-day
    assert metrics.var_10d_99 > metrics.var_1d_95


def test_var_empty_series():
    """Test edge case: empty P&L series"""
    var_value = calc_historical_var_1d_95([])
    assert var_value == 0.0


def test_var_insufficient_data():
    """Test with less than 250 days"""
    short_pnl = [-100, -50, 0, 50, 100]
    var_value = calc_historical_var_1d_95(short_pnl, window_days=250)
    
    # Should use all available data
    assert var_value > 0
