import json
import sqlite3
import json
from typing import Optional
from app.core.logging import logger
from app.core.exceptions import DatabaseError
from app.core.logging import logger


class FeedbackRepository:
    """Feedback repository managing user ratings in SQLite database."""

    @staticmethod
    def insert_feedback(conn: sqlite3.Connection, feedback: dict) -> None:
        query = """
        INSERT INTO feedback (
            feedback_id, query, answer, rating, comment, 
            sources_used, session_id, query_type, retry_count, 
            response_time_ms, created_at
        ) VALUES (
            :feedback_id, :query, :answer, :rating, :comment, 
            :sources_used, :session_id, :query_type, :retry_count, 
            :response_time_ms, :created_at
        )
        """
        try:
            # Prepare sources_used list into JSON string
            if isinstance(feedback.get("sources_used"), list):
                feedback["sources_used"] = json.dumps(feedback["sources_used"])
                
            conn.execute(query, feedback)
            logger.info(f"Inserted feedback record: {feedback['feedback_id']} in SQLite feedback table.")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert feedback: {e}")
            raise DatabaseError(f"Database write failed: {e}")

    @staticmethod
    def list_feedback(conn: sqlite3.Connection, rating: Optional[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
        if rating and rating != "all":
            query = "SELECT * FROM feedback WHERE rating = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (rating, limit, offset)
        else:
            query = "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (limit, offset)
            
        try:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                item = dict(row)
                if item.get("sources_used"):
                    try:
                        item["sources_used"] = json.loads(item["sources_used"])
                    except Exception:
                        pass
                results.append(item)
            return results
        except sqlite3.Error as e:
            logger.error(f"Failed to list feedback records: {e}")
            raise DatabaseError(f"Database read failed: {e}")

    @staticmethod
    def count_feedback(conn: sqlite3.Connection, rating: Optional[str] = None) -> int:
        if rating and rating != "all":
            query = "SELECT COUNT(*) FROM feedback WHERE rating = ?"
            params = (rating,)
        else:
            query = "SELECT COUNT(*) FROM feedback"
            params = ()
            
        try:
            count = conn.execute(query, params).fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(f"Failed to count feedback records: {e}")
            raise DatabaseError(f"Database count failed: {e}")
