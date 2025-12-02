"""
ETL: News ingestion from Bloomberg/Refinitiv/RSS
Fetches news events, ratings changes, sanctions
"""
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.db.models import NewsEvent, Issuer
from app.db.session import async_session_maker

logger = structlog.get_logger()


async def fetch_news_from_bloomberg(issuers: List[str]) -> List[Dict]:
    """
    Fetch news from Bloomberg News API
    
    TODO: Implement real Bloomberg News API
    For now, returns mock data
    
    Args:
        issuers: List of issuer names to monitor
    
    Returns:
        List of news events
    """
    logger.info("fetching_bloomberg_news", issuers_count=len(issuers))
    
    # Mock data - replace with real Bloomberg News API
    mock_news = [
        {
            'headline': 'Kazakhstan upgrades sovereign rating outlook to positive',
            'content': 'S&P Global Ratings upgraded Kazakhstan...',
            'issuer_name': 'REPUBLIC OF KAZAKHSTAN',
            'event_type': 'RATING_CHANGE',
            'severity': 'POSITIVE',
            'importance': 4,
            'source': 'Bloomberg',
        },
        {
            'headline': 'Navoiy MMC reports Q4 earnings miss',
            'content': 'Navoiy Mining reported lower than expected...',
            'issuer_name': 'NAVOIY MMC',
            'event_type': 'EARNINGS',
            'severity': 'NEGATIVE',
            'importance': 3,
            'source': 'Bloomberg',
        },
    ]
    
    return mock_news


async def fetch_news_from_rss(feed_urls: List[str]) -> List[Dict]:
    """
    Fetch news from RSS feeds
    
    Args:
        feed_urls: List of RSS feed URLs
    
    Returns:
        List of news events
    """
    logger.info("fetching_rss_news", feeds_count=len(feed_urls))
    
    # TODO: Implement RSS parsing
    # import feedparser
    # for url in feed_urls:
    #     feed = feedparser.parse(url)
    #     ...
    
    return []


async def classify_news_sentiment(headline: str, content: str) -> str:
    """
    Classify news sentiment (POSITIVE/NEUTRAL/NEGATIVE)
    
    TODO: Integrate with NLP/AI service or use simple keyword matching
    """
    negative_keywords = ['miss', 'downgrade', 'sanctions', 'default', 'loss', 'weak']
    positive_keywords = ['upgrade', 'strong', 'beat', 'growth', 'positive']
    
    text = (headline + ' ' + content).lower()
    
    neg_count = sum(1 for kw in negative_keywords if kw in text)
    pos_count = sum(1 for kw in positive_keywords if kw in text)
    
    if pos_count > neg_count:
        return 'POSITIVE'
    elif neg_count > pos_count:
        return 'NEGATIVE'
    else:
        return 'NEUTRAL'


async def match_issuer(issuer_name: str, session: AsyncSession) -> int | None:
    """Match news to issuer by name"""
    result = await session.execute(
        select(Issuer).where(Issuer.name.ilike(f'%{issuer_name}%'))
    )
    issuer = result.scalar_one_or_none()
    return issuer.id if issuer else None


async def save_news_events(
    session: AsyncSession,
    news_items: List[Dict],
) -> int:
    """Save news events to database"""
    count = 0
    
    for item in news_items:
        # Match issuer
        issuer_id = None
        if item.get('issuer_name'):
            issuer_id = await match_issuer(item['issuer_name'], session)
        
        # Classify sentiment if not provided
        if 'severity' not in item:
            item['severity'] = await classify_news_sentiment(
                item.get('headline', ''),
                item.get('content', ''),
            )
        
        event = NewsEvent(
            event_date=datetime.utcnow(),
            source=item.get('source', 'UNKNOWN'),
            headline=item['headline'],
            content=item.get('content'),
            issuer_id=issuer_id,
            event_type=item.get('event_type'),
            severity=item.get('severity', 'NEUTRAL'),
            importance=item.get('importance', 3),
        )
        session.add(event)
        count += 1
    
    await session.commit()
    logger.info("saved_news_events", count=count)
    return count


async def fetch_news():
    """
    Main ETL job: fetch news from multiple sources
    
    Steps:
    1. Get monitored issuers
    2. Fetch from Bloomberg/Refinitiv/RSS
    3. Classify sentiment
    4. Match to issuers/counterparties
    5. Save to database
    """
    logger.info("fetch_news_job_started")
    
    try:
        async with async_session_maker() as session:
            # 1. Get monitored issuers
            result = await session.execute(select(Issuer))
            issuers = result.scalars().all()
            issuer_names = [i.name for i in issuers]
            
            logger.info("monitoring_issuers", count=len(issuer_names))
            
            # 2. Fetch news
            bloomberg_news = await fetch_news_from_bloomberg(issuer_names)
            rss_news = await fetch_news_from_rss([
                'https://example.com/rss/finance',
            ])
            
            all_news = bloomberg_news + rss_news
            
            if not all_news:
                logger.info("no_news_fetched")
                return
            
            # 3. Save
            await save_news_events(session, all_news)
            
            logger.info("fetch_news_job_complete", total_news=len(all_news))
            
    except Exception as e:
        logger.error("fetch_news_job_failed", error=str(e), exc_info=True)
        raise
