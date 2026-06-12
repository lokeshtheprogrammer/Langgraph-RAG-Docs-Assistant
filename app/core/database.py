import os
import sqlite3
from contextlib import contextmanager

from app.config import settings
from app.core.exceptions import DatabaseError
from app.core.logging import logger

# DDL schemas
DOCUMENTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    source_url TEXT DEFAULT '',
    file_hash TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'indexed',
    ingestion_timestamp TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    error_message TEXT DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

FEEDBACK_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_id TEXT NOT NULL UNIQUE,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    rating TEXT NOT NULL,
    comment TEXT DEFAULT NULL,
    sources_used TEXT DEFAULT NULL,
    session_id TEXT DEFAULT NULL,
    query_type TEXT DEFAULT NULL,
    retry_count INTEGER DEFAULT 0,
    response_time_ms INTEGER DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

CHAT_HISTORY_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

QUERY_LOG_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    query_type TEXT DEFAULT NULL,
    rewritten_query TEXT DEFAULT NULL,
    retry_count INTEGER DEFAULT 0,
    is_fallback INTEGER DEFAULT 0,
    web_search_used INTEGER DEFAULT 0,
    hallucination_score REAL DEFAULT NULL,
    confidence_score REAL DEFAULT NULL,
    response_time_ms INTEGER DEFAULT NULL,
    source_count INTEGER DEFAULT 0,
    session_id TEXT DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

INDICES_DDL = [
    "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);",
    "CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);",
    "CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);",
    "CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_query_log_created ON query_log(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_query_log_query_type ON query_log(query_type);"
]

@contextmanager
def get_db_connection():
    """Context manager for obtaining thread-safe SQLite connection."""
    db_path = settings.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # Enable dictionary cursor representation
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"SQLite database error: {e}", extra={"extra": {"db_path": db_path}})
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        if conn:
            conn.close()

def initialize_db() -> None:
    """Initialize database tables and indices idempotently."""
    logger.info("Initializing SQLite database schemas...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(DOCUMENTS_TABLE_DDL)
            cursor.execute(FEEDBACK_TABLE_DDL)
            cursor.execute(CHAT_HISTORY_TABLE_DDL)
            cursor.execute(QUERY_LOG_TABLE_DDL)
            for index_query in INDICES_DDL:
                cursor.execute(index_query)
            logger.info("Database schemas initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error during schema creation: {e}")
            raise DatabaseError(f"Failed to create database schemas: {e}") from e
