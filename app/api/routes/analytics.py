from fastapi import APIRouter

from app.core.database import get_db_connection
from app.core.logging import logger
from app.repositories.query_log_repository import QueryLogRepository

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_analytics_summary():
    """Return aggregate query analytics: latency, confidence, fallback rates, and retry stats."""
    logger.info("Fetching analytics summary...")
    with get_db_connection() as conn:
        summary = QueryLogRepository.get_summary(conn)
    return summary


@router.get("/query-types")
async def get_query_type_distribution():
    """Return query count distribution grouped by query_type (conceptual, how-to, etc.)."""
    logger.info("Fetching query type distribution...")
    with get_db_connection() as conn:
        distribution = QueryLogRepository.get_query_type_distribution(conn)
    return {"query_types": distribution}


@router.get("/recent")
async def get_recent_queries(limit: int = 20):
    """Return the most recent query log entries for audit and debugging."""
    logger.info(f"Fetching {limit} recent query logs...")
    with get_db_connection() as conn:
        queries = QueryLogRepository.get_recent_queries(conn, limit=min(limit, 100))
    return {"queries": queries}
