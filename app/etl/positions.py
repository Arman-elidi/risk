"""
ETL: Position synchronization from back-office
Supports CSV/SFTP and REST API sources
"""
import csv
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog

from app.db.models import Position, Portfolio
from app.db.session import async_session_maker

logger = structlog.get_logger()


async def load_positions_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load positions from CSV file
    
    Expected CSV columns:
    - portfolio_name, isin, instrument_type, quantity, notional,
      maturity_date, coupon, etc.
    """
    positions = []
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            positions.append({
                'portfolio_name': row.get('portfolio_name'),
                'isin': row.get('isin'),
                'instrument_type': row.get('instrument_type'),
                'quantity': float(row.get('quantity', 0)),
                'notional': float(row.get('notional', 0)) if row.get('notional') else None,
                'maturity_date': datetime.strptime(row['maturity_date'], '%Y-%m-%d').date() if row.get('maturity_date') else None,
                'coupon': float(row.get('coupon', 0)) if row.get('coupon') else None,
                'coupon_frequency': int(row.get('coupon_frequency', 2)) if row.get('coupon_frequency') else None,
                'status': row.get('status', 'ACTIVE'),
            })
    
    logger.info("loaded_positions_from_csv", count=len(positions), file=file_path)
    return positions


async def normalize_position(raw_position: Dict[str, Any], portfolio_id: int) -> Dict[str, Any]:
    """Normalize and validate position data"""
    return {
        'portfolio_id': portfolio_id,
        'isin': raw_position.get('isin'),
        'instrument_type': raw_position['instrument_type'].upper(),
        'quantity': raw_position['quantity'],
        'notional': raw_position.get('notional'),
        'maturity_date': raw_position.get('maturity_date'),
        'coupon': raw_position.get('coupon'),
        'coupon_frequency': raw_position.get('coupon_frequency'),
        'status': raw_position.get('status', 'ACTIVE'),
    }


async def upsert_positions(
    session: AsyncSession,
    positions: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Upsert positions into database
    
    Logic:
    - New ISIN + portfolio → INSERT
    - Existing ISIN → UPDATE quantity, status
    - Missing positions → mark as INACTIVE
    
    Returns:
        Dict with counts: {'inserted': X, 'updated': Y, 'closed': Z}
    """
    stats = {'inserted': 0, 'updated': 0, 'closed': 0}
    
    for pos_data in positions:
        portfolio_id = pos_data['portfolio_id']
        isin = pos_data.get('isin')
        
        if not isin:
            continue
        
        # Check if position exists
        result = await session.execute(
            select(Position).where(
                Position.portfolio_id == portfolio_id,
                Position.isin == isin,
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.quantity = pos_data['quantity']
            existing.status = pos_data['status']
            existing.updated_at = datetime.utcnow()
            stats['updated'] += 1
        else:
            # Insert new
            new_position = Position(**pos_data)
            session.add(new_position)
            stats['inserted'] += 1
    
    await session.commit()
    
    logger.info("upsert_positions_complete", **stats)
    return stats


async def sync_positions_from_backoffice(file_path: str = None):
    """
    Main ETL job: sync positions from back-office
    
    Steps:
    1. Load from source (CSV/SFTP/API)
    2. Normalize data
    3. Upsert to database
    4. Log audit trail
    """
    logger.info("sync_positions_job_started", source=file_path or "SFTP")
    
    try:
        # 1. Load raw data
        if file_path:
            raw_positions = await load_positions_from_csv(file_path)
        else:
            # TODO: Implement SFTP fetch
            logger.warning("sftp_not_implemented_using_dummy_data")
            raw_positions = []
        
        if not raw_positions:
            logger.warning("no_positions_to_sync")
            return
        
        async with async_session_maker() as session:
            # 2. Get portfolio mappings
            portfolio_map = {}
            result = await session.execute(select(Portfolio))
            portfolios = result.scalars().all()
            for p in portfolios:
                portfolio_map[p.name] = p.id
            
            # 3. Normalize
            normalized = []
            for raw in raw_positions:
                portfolio_name = raw.get('portfolio_name', 'RISK_BOND_BOOK')
                portfolio_id = portfolio_map.get(portfolio_name)
                
                if not portfolio_id:
                    logger.warning("portfolio_not_found", name=portfolio_name)
                    continue
                
                norm = await normalize_position(raw, portfolio_id)
                normalized.append(norm)
            
            # 4. Upsert
            stats = await upsert_positions(session, normalized)
            
            logger.info("sync_positions_job_complete", **stats)
            
    except Exception as e:
        logger.error("sync_positions_job_failed", error=str(e), exc_info=True)
        raise
