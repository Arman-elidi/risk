"""
ETL: Market data ingestion from Bloomberg/Refinitiv
Fetches prices, yields, spreads, FX, curves, vols
"""
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.db.models import MarketDataSnapshot, YieldCurve, VolSurface, Position
from app.db.session import async_session_maker

logger = structlog.get_logger()


async def fetch_prices_from_bloomberg(isins: List[str]) -> Dict[str, Dict]:
    """
    Fetch market prices from Bloomberg BLPAPI
    
    TODO: Implement real Bloomberg API integration
    For now, returns mock data
    
    Args:
        isins: List of ISINs to fetch
    
    Returns:
        Dict mapping ISIN -> price data
    """
    logger.info("fetching_bloomberg_prices", count=len(isins))
    
    # Mock data - replace with real Bloomberg API call
    # import blpapi
    # session = blpapi.Session()
    # ...
    
    mock_data = {}
    for isin in isins:
        mock_data[isin] = {
            'price': 100.0,
            'yield_pct': 0.05,
            'spread_bps': 150.0,
            'bid_price': 99.8,
            'ask_price': 100.2,
            'bid_ask_spread_bps': 20.0,
            'volume': 1_000_000.0,
            'liquidity_score': 0.75,
        }
    
    return mock_data


async def fetch_yield_curves(currencies: List[str], as_of_date: date) -> Dict[str, Dict]:
    """
    Fetch yield curves for given currencies
    
    Returns:
        Dict mapping currency -> curve data
    """
    logger.info("fetching_yield_curves", currencies=currencies)
    
    # Mock data
    curves = {}
    for ccy in currencies:
        curves[ccy] = {
            'tenors': [0.25, 0.5, 1, 2, 5, 10, 30],
            'rates': [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04],
        }
    
    return curves


async def fetch_vol_surfaces(underlyings: List[str], as_of_date: date) -> Dict[str, Dict]:
    """
    Fetch volatility surfaces for options
    
    Returns:
        Dict mapping underlying -> vol surface
    """
    logger.info("fetching_vol_surfaces", underlyings=underlyings)
    
    # Mock data
    surfaces = {}
    for underlying in underlyings:
        surfaces[underlying] = {
            'strikes': [90, 95, 100, 105, 110],
            'expiries': [0.25, 0.5, 1.0],
            'vols': [
                [0.25, 0.22, 0.20, 0.22, 0.25],
                [0.23, 0.20, 0.18, 0.20, 0.23],
                [0.21, 0.19, 0.17, 0.19, 0.21],
            ],
        }
    
    return surfaces


async def save_market_data_snapshots(
    session: AsyncSession,
    snapshots: List[Dict[str, Any]],
    as_of_date: date,
) -> int:
    """Save market data snapshots to database"""
    count = 0
    
    for snap in snapshots:
        snapshot = MarketDataSnapshot(
            snapshot_date=as_of_date,
            snapshot_time=datetime.utcnow(),
            **snap
        )
        session.add(snapshot)
        count += 1
    
    await session.commit()
    logger.info("saved_market_data_snapshots", count=count)
    return count


async def save_yield_curves(
    session: AsyncSession,
    curves: Dict[str, Dict],
    as_of_date: date,
) -> int:
    """Save yield curves to database"""
    count = 0
    
    for ccy, curve_data in curves.items():
        curve = YieldCurve(
            curve_id=f"{ccy}_GOVT",
            as_of_date=as_of_date,
            currency=ccy,
            tenors_rates_json=curve_data,
        )
        session.add(curve)
        count += 1
    
    await session.commit()
    logger.info("saved_yield_curves", count=count)
    return count


async def save_vol_surfaces(
    session: AsyncSession,
    surfaces: Dict[str, Dict],
    as_of_date: date,
) -> int:
    """Save vol surfaces to database"""
    count = 0
    
    for underlying, surface_data in surfaces.items():
        surface = VolSurface(
            surface_id=f"{underlying}_VOL",
            as_of_date=as_of_date,
            underlying=underlying,
            surface_json=surface_data,
        )
        session.add(surface)
        count += 1
    
    await session.commit()
    logger.info("saved_vol_surfaces", count=count)
    return count


async def fetch_market_data():
    """
    Main ETL job: fetch market data from Bloomberg/Refinitiv
    
    Steps:
    1. Get all active positions (ISINs)
    2. Fetch prices, spreads, vols
    3. Fetch curves and vol surfaces
    4. Save to database
    """
    logger.info("fetch_market_data_job_started")
    as_of_date = date.today()
    
    try:
        async with async_session_maker() as session:
            # 1. Get all active ISINs
            result = await session.execute(
                select(Position).where(Position.status == 'ACTIVE')
            )
            positions = result.scalars().all()
            
            isins = list(set([p.isin for p in positions if p.isin]))
            logger.info("fetching_market_data_for_isins", count=len(isins))
            
            if not isins:
                logger.warning("no_active_positions_found")
                return
            
            # 2. Fetch prices
            price_data = await fetch_prices_from_bloomberg(isins)
            
            # 3. Prepare snapshots
            snapshots = []
            for isin, data in price_data.items():
                snapshots.append({
                    'isin': isin,
                    **data
                })
            
            # 4. Save market data
            await save_market_data_snapshots(session, snapshots, as_of_date)
            
            # 5. Fetch and save curves
            currencies = ['USD', 'EUR']
            curves = await fetch_yield_curves(currencies, as_of_date)
            await save_yield_curves(session, curves, as_of_date)
            
            # 6. Fetch and save vol surfaces
            underlyings = ['EURUSD', 'USDJPY']
            surfaces = await fetch_vol_surfaces(underlyings, as_of_date)
            await save_vol_surfaces(session, surfaces, as_of_date)
            
            logger.info("fetch_market_data_job_complete")
            
    except Exception as e:
        logger.error("fetch_market_data_job_failed", error=str(e), exc_info=True)
        raise
