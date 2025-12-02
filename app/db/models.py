"""
SQLAlchemy database models for risk-service
All tables according to technical specification
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    portfolio_type = Column(String(50), nullable=False)  # BOND_DEALER, DERIVATIVES_CLIENT, etc.
    base_currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)  # ACTIVE, FROZEN, CLOSED
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio")
    risk_snapshots = relationship("RiskSnapshot", back_populates="portfolio")
    limits = relationship("Limit", back_populates="portfolio")


class Counterparty(Base):
    __tablename__ = "counterparties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    lei = Column(String(20), nullable=True, unique=True)  # Legal Entity Identifier
    counterparty_type = Column(String(50), nullable=False)  # BANK, BROKER, CLIENT
    country = Column(String(3), nullable=True)
    rating_sp = Column(String(10), nullable=True)
    rating_moodys = Column(String(10), nullable=True)
    rating_fitch = Column(String(10), nullable=True)
    internal_rating = Column(String(10), nullable=True)
    wwr_flag = Column(Boolean, default=False)  # Wrong-Way Risk flag
    created_at = Column(DateTime, default=datetime.utcnow)


class Issuer(Base):
    __tablename__ = "issuers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    country = Column(String(3), nullable=True, index=True)
    sector = Column(String(100), nullable=True, index=True)
    rating_sp = Column(String(10), nullable=True)
    rating_moodys = Column(String(10), nullable=True)
    rating_fitch = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Instrument identification
    instrument_id = Column(String(50), nullable=True)
    isin = Column(String(12), nullable=True, index=True)
    bloomberg_ticker = Column(String(50), nullable=True)
    instrument_type = Column(String(50), nullable=False, index=True)  # BOND, FX_FORWARD, etc.
    
    # Position sizing
    quantity = Column(Float, nullable=False)
    notional = Column(Float, nullable=True)
    direction = Column(String(10), nullable=True)  # LONG, SHORT, PAY, RECEIVE
    
    # Bond-specific
    maturity_date = Column(Date, nullable=True)
    coupon = Column(Float, nullable=True)
    coupon_frequency = Column(Integer, nullable=True)
    fixed_or_float = Column(String(10), nullable=True)
    day_count = Column(String(20), nullable=True)
    
    # Derivative-specific
    underlying = Column(String(50), nullable=True)
    strike = Column(Float, nullable=True)
    option_type = Column(String(10), nullable=True)  # CALL, PUT
    exercise_type = Column(String(20), nullable=True)  # EUROPEAN, AMERICAN
    
    # Parties
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=True, index=True)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True, index=True)
    
    # Dates & pricing
    trade_date = Column(Date, nullable=True)
    settlement_date = Column(Date, nullable=True)
    acquisition_price = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    
    __table_args__ = (
        Index("idx_portfolio_active", "portfolio_id", "status"),
    )


class MarketDataSnapshot(Base):
    __tablename__ = "market_data_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow)
    
    # Instrument
    instrument_id = Column(String(50), nullable=True, index=True)
    isin = Column(String(12), nullable=True, index=True)
    
    # Pricing
    price = Column(Float, nullable=True)
    yield_pct = Column(Float, nullable=True)
    spread_bps = Column(Float, nullable=True)
    bid_price = Column(Float, nullable=True)
    ask_price = Column(Float, nullable=True)
    bid_ask_spread_bps = Column(Float, nullable=True)
    
    # Liquidity
    volume = Column(Float, nullable=True)
    liquidity_score = Column(Float, nullable=True)
    days_since_trade = Column(Integer, nullable=True)
    
    # Risk metrics
    implied_vol = Column(Float, nullable=True)
    fx_rate = Column(Float, nullable=True)
    credit_spread_bps = Column(Float, nullable=True)
    cds_spread_5y_bps = Column(Float, nullable=True)
    recovery_rate = Column(Float, nullable=True)
    
    __table_args__ = (
        Index("idx_snapshot_date_instrument", "snapshot_date", "instrument_id"),
    )


class YieldCurve(Base):
    __tablename__ = "yield_curves"
    
    id = Column(Integer, primary_key=True, index=True)
    curve_id = Column(String(50), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)
    currency = Column(String(3), nullable=False)
    tenors_rates_json = Column(JSON, nullable=False)  # {"tenors": [...], "rates": [...]}
    created_at = Column(DateTime, default=datetime.utcnow)


class VolSurface(Base):
    __tablename__ = "vol_surfaces"
    
    id = Column(Integer, primary_key=True, index=True)
    surface_id = Column(String(50), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)
    underlying = Column(String(50), nullable=False)
    surface_json = Column(JSON, nullable=False)  # {"strikes": [...], "expiries": [...], "vols": [[...]]}
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    calculation_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Market risk
    var_1d_95 = Column(Float, nullable=True)
    stressed_var = Column(Float, nullable=True)
    dv01_total = Column(Float, nullable=True)
    duration = Column(Float, nullable=True)
    convexity = Column(Float, nullable=True)
    
    # Credit risk
    total_exposure = Column(Float, nullable=True)
    credit_var = Column(Float, nullable=True)
    cva_total = Column(Float, nullable=True)
    expected_loss = Column(Float, nullable=True)
    
    # CCR
    pfe_current = Column(Float, nullable=True)
    pfe_peak = Column(Float, nullable=True)
    ead_total = Column(Float, nullable=True)
    
    # Liquidity
    liquidation_cost_1d = Column(Float, nullable=True)
    liquidation_cost_5d = Column(Float, nullable=True)
    liquidity_score = Column(Float, nullable=True)
    lcr_ratio = Column(Float, nullable=True)
    funding_gap_short_term = Column(Float, nullable=True)
    
    # Capital
    k_npr = Column(Float, nullable=True)
    k_aum = Column(Float, nullable=True)
    k_cmh = Column(Float, nullable=True)
    k_coh = Column(Float, nullable=True)
    total_k_req = Column(Float, nullable=True)
    own_funds = Column(Float, nullable=True)
    capital_ratio = Column(Float, nullable=True)
    
    # Status
    calculation_status = Column(String(20), nullable=False, default="COMPLETED")  # COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    engine_version = Column(String(20), nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="risk_snapshots")
    
    __table_args__ = (
        Index("idx_portfolio_date", "portfolio_id", "snapshot_date"),
    )


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)
    risk_snapshot_id = Column(Integer, ForeignKey("risk_snapshots.id"), nullable=True)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=True)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # LIMIT_BREACH, ANOMALY, RATING_CHANGE, etc.
    severity = Column(String(20), nullable=False, index=True)  # GREEN, YELLOW, RED, CRITICAL
    metric_name = Column(String(100), nullable=True)
    current_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    
    # Acknowledgement
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_severity_created", "severity", "created_at"),
    )


class Limit(Base):
    __tablename__ = "limits"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Limit definition
    limit_type = Column(String(50), nullable=False, index=True)  # DV01, VaR, K, LCR, etc.
    metric_name = Column(String(100), nullable=False)
    limit_value = Column(Float, nullable=False)
    warning_threshold = Column(Float, nullable=False)  # % of limit
    critical_threshold = Column(Float, nullable=False)  # % of limit
    
    # Status
    active = Column(Boolean, default=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="limits")


class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # UPDATE_LIMIT, OVERRIDE_ALERT, etc.
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(50), nullable=True)


class VaRBacktesting(Base):
    __tablename__ = "var_backtesting"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    var_1d_95_forecast = Column(Float, nullable=False)
    pnl_realized = Column(Float, nullable=True)
    is_exception = Column(Boolean, default=False)  # True if loss > VaR
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_portfolio_date_bt", "portfolio_id", "date"),
    )


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    instrument_id = Column(String(50), nullable=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    issue_type = Column(String(50), nullable=False, index=True)  # PRICE_JUMP, STALE_QUOTE, MISSING_FX, etc.
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    details = Column(Text, nullable=True)
    resolved_flag = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsEvent(Base):
    __tablename__ = "news_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_date = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=True)  # Bloomberg, Refinitiv, RSS, etc.
    headline = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    
    # Links
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=True, index=True)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    country = Column(String(3), nullable=True, index=True)
    sector = Column(String(100), nullable=True)
    
    # Classification
    event_type = Column(String(50), nullable=True)  # RATING_CHANGE, EARNINGS, SANCTIONS, etc.
    severity = Column(String(20), nullable=True)  # POSITIVE, NEUTRAL, NEGATIVE
    importance = Column(Integer, nullable=True)  # 1-5 scale
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_issuer_date", "issuer_id", "event_date"),
    )


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="VIEWER")  # ADMIN, RISK, TRADER, VIEWER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
