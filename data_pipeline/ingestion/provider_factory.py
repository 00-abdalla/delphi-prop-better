"""Factory for creating NBA data providers."""
from backend.app.config import settings
from backend.app.logging_config import get_logger
from data_pipeline.ingestion.nba_api_provider import NBAApiProvider
from data_pipeline.ingestion.nba_mock_provider import BaseNBAProvider, NBAMockProvider

logger = get_logger(__name__)


def get_nba_provider() -> BaseNBAProvider:
    """
    Get NBA data provider based on configuration.
    
    Returns:
        NBAApiProvider if USE_REAL_NBA_DATA=True, otherwise NBAMockProvider
    """
    if settings.USE_REAL_NBA_DATA:
        logger.info("Using real NBA API provider")
        return NBAApiProvider(rate_limit_calls_per_minute=settings.NBA_API_RATE_LIMIT)
    else:
        logger.info("Using mock NBA provider")
        return NBAMockProvider()
