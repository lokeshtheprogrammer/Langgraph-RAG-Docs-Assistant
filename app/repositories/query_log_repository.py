import sqlite3

from app.core.exceptions import DatabaseError
from app.core.logging import logger


class QueryLogRepository:
    """Repository for logging and querying pipeline execution metrics."""

    @staticmethod
    def insert_log(conn: sqlite3.Connection, entry: dict) -> None:
        """Persist a query execution log entry."""
        query = """
        INSERT INTO query_log (
            question, query_type, rewritten_query, retry_count,
            is_fallback, web_search_used, hallucination_score,
            confidence_score, response_time_ms, source_count, session_id
        ) VALUES (
            :question, :query_type, :rewritten_query, :retry_count,
            :is_fallback, :web_search_used, :hallucination_score,
            :confidence_score, :response_time_ms, :source_count, :session_id
        )
        """
        try:
            conn.execute(query, entry)
            logger.info("Logged query execution to query_log table.")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert query log: {e}")
            raise DatabaseError(f"Query log write failed: {e}") from e

    @staticmethod
    def get_summary(conn: sqlite3.Connection) -> dict:
        """Return aggregate analytics across all logged queries."""
        try:
            total = conn.execute("SELECT COUNT(*) FROM query_log").fetchone()[0]

            avg_latency = conn.execute(
                "SELECT AVG(response_time_ms) FROM query_log WHERE response_time_ms IS NOT NULL"
            ).fetchone()[0]

            p95_latency = conn.execute(
                """SELECT response_time_ms FROM query_log
                   WHERE response_time_ms IS NOT NULL
                   ORDER BY response_time_ms DESC
                   LIMIT 1 OFFSET (
                       SELECT CAST(COUNT(*) * 0.05 AS INTEGER)
                       FROM query_log WHERE response_time_ms IS NOT NULL
                   )"""
            ).fetchone()

            avg_confidence = conn.execute(
                "SELECT AVG(confidence_score) FROM query_log WHERE confidence_score IS NOT NULL"
            ).fetchone()[0]

            avg_hallucination = conn.execute(
                "SELECT AVG(hallucination_score) FROM query_log WHERE hallucination_score IS NOT NULL"
            ).fetchone()[0]

            fallback_count = conn.execute(
                "SELECT COUNT(*) FROM query_log WHERE is_fallback = 1"
            ).fetchone()[0]

            web_search_count = conn.execute(
                "SELECT COUNT(*) FROM query_log WHERE web_search_used = 1"
            ).fetchone()[0]

            avg_retries = conn.execute(
                "SELECT AVG(retry_count) FROM query_log"
            ).fetchone()[0]

            return {
                "total_queries": total,
                "avg_response_time_ms": round(avg_latency, 1) if avg_latency else 0,
                "p95_response_time_ms": p95_latency[0] if p95_latency else 0,
                "avg_confidence_score": round(avg_confidence, 3) if avg_confidence else 0,
                "avg_hallucination_score": round(avg_hallucination, 3) if avg_hallucination else 0,
                "fallback_rate": round(fallback_count / total, 3) if total > 0 else 0,
                "web_search_rate": round(web_search_count / total, 3) if total > 0 else 0,
                "avg_retry_count": round(avg_retries, 2) if avg_retries else 0,
            }
        except sqlite3.Error as e:
            logger.error(f"Failed to compute query analytics: {e}")
            raise DatabaseError(f"Analytics query failed: {e}") from e

    @staticmethod
    def get_query_type_distribution(conn: sqlite3.Connection) -> list[dict]:
        """Return query counts grouped by query_type."""
        try:
            rows = conn.execute(
                """SELECT query_type, COUNT(*) as count
                   FROM query_log
                   WHERE query_type IS NOT NULL
                   GROUP BY query_type
                   ORDER BY count DESC"""
            ).fetchall()
            return [{"query_type": row["query_type"], "count": row["count"]} for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get query type distribution: {e}")
            raise DatabaseError(f"Analytics query failed: {e}") from e

    @staticmethod
    def get_recent_queries(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
        """Return the most recent query log entries."""
        try:
            rows = conn.execute(
                """SELECT question, query_type, retry_count, is_fallback,
                          web_search_used, hallucination_score, confidence_score,
                          response_time_ms, source_count, created_at
                   FROM query_log
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent queries: {e}")
            raise DatabaseError(f"Analytics query failed: {e}") from e
