"""
Scheduled jobs using APScheduler
Nightly batch ETL and risk calculations
"""
import asyncio
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from app.etl.positions import sync_positions_from_backoffice
from app.etl.market_data import fetch_market_data
from app.etl.news import fetch_news
from app.services.pdf_report import generate_daily_pdf
from app.db.session import async_session_maker

logger = structlog.get_logger()

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def generate_pdf_job():
    """Wrapper for PDF generation job"""
    async with async_session_maker() as session:
        await generate_daily_pdf(session, date.today())


def setup_jobs():
    """Configure all scheduled jobs"""
    
    # 1. Positions sync: 22:30 UTC daily
    scheduler.add_job(
        sync_positions_from_backoffice,
        trigger=CronTrigger(hour=22, minute=30, timezone='UTC'),
        id='sync_positions',
        name='Sync positions from back-office',
        replace_existing=True,
    )
    logger.info("scheduled_job_added", job_id="sync_positions", schedule="22:30 UTC")
    
    # 2. Market data fetch: 23:00 UTC daily
    scheduler.add_job(
        fetch_market_data,
        trigger=CronTrigger(hour=23, minute=0, timezone='UTC'),
        id='fetch_market_data',
        name='Fetch market data from Bloomberg',
        replace_existing=True,
    )
    logger.info("scheduled_job_added", job_id="fetch_market_data", schedule="23:00 UTC")
    
    # 3. News fetch: Every 30 minutes during trading hours (09:00-17:00 UTC)
    scheduler.add_job(
        fetch_news,
        trigger=CronTrigger(minute='*/30', hour='9-17', timezone='UTC'),
        id='fetch_news',
        name='Fetch news from sources',
        replace_existing=True,
    )
    logger.info("scheduled_job_added", job_id="fetch_news", schedule="Every 30m (9-17 UTC)")
    
    # 4. Daily PDF report: 01:00 UTC (after risk calculations)
    scheduler.add_job(
        generate_pdf_job,
        trigger=CronTrigger(hour=1, minute=0, timezone='UTC'),
        id='generate_daily_pdf',
        name='Generate daily PDF report',
        replace_existing=True,
    )
    logger.info("scheduled_job_added", job_id="generate_daily_pdf", schedule="01:00 UTC")
    
    # 5. Nightly risk calculation: 00:00 UTC (after market data is ready)
    # This will be added in Step 5 when risk engine is ready
    # scheduler.add_job(
    #     calculate_nightly_risks,
    #     trigger=CronTrigger(hour=0, minute=0, timezone='UTC'),
    #     id='nightly_risk_calc',
    #     name='Nightly risk calculation',
    #     replace_existing=True,
    # )


def start_scheduler():
    """Start the scheduler"""
    setup_jobs()
    scheduler.start()
    logger.info("scheduler_started", jobs_count=len(scheduler.get_jobs()))


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown(wait=True)
    logger.info("scheduler_stopped")


def get_scheduler():
    """Get scheduler instance (for testing/manual control)"""
    return scheduler
