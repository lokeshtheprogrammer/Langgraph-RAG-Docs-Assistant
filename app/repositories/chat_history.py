import sqlite3

from app.core.exceptions import DatabaseError
from app.core.logging import logger


class ChatHistoryRepository:
    """Repository for managing session-based conversation memory in SQLite."""

    @staticmethod
    def insert_turn(conn: sqlite3.Connection, session_id: str, role: str, content: str) -> None:
        query = """
        INSERT INTO chat_history (session_id, role, content)
        VALUES (?, ?, ?)
        """
        try:
            conn.execute(query, (session_id, role, content))
            logger.info(f"Inserted chat turn for session {session_id} (role={role})")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert chat turn: {e}")
            raise DatabaseError(f"Database write failed: {e}") from e

    @staticmethod
    def get_history(conn: sqlite3.Connection, session_id: str, limit: int = 10) -> list[dict]:
        query = """
        SELECT role, content, created_at 
        FROM chat_history 
        WHERE session_id = ? 
        ORDER BY id DESC 
        LIMIT ?
        """
        try:
            rows = conn.execute(query, (session_id, limit)).fetchall()
            # Return in chronological order (oldest first)
            return [dict(row) for row in reversed(rows)]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve chat history: {e}")
            raise DatabaseError(f"Database read failed: {e}") from e

    @staticmethod
    def clear_history(conn: sqlite3.Connection, session_id: str) -> None:
        query = "DELETE FROM chat_history WHERE session_id = ?"
        try:
            conn.execute(query, (session_id,))
            logger.info(f"Cleared chat history for session {session_id}")
        except sqlite3.Error as e:
            logger.error(f"Failed to clear chat history: {e}")
            raise DatabaseError(f"Database delete failed: {e}") from e
