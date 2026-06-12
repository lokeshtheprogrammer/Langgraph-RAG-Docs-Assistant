import sqlite3
from datetime import datetime

from app.core.exceptions import DatabaseError
from app.core.logging import logger


class DocumentRepository:
    """Registry repository managing documents metadata in SQLite database."""

    @staticmethod
    def insert_document(conn: sqlite3.Connection, doc: dict) -> None:
        query = """
        INSERT INTO documents (
            id, filename, source_url, file_hash, file_size_bytes, 
            file_type, chunk_count, status, ingestion_timestamp, 
            embedding_model, error_message
        ) VALUES (
            :id, :filename, :source_url, :file_hash, :file_size_bytes, 
            :file_type, :chunk_count, :status, :ingestion_timestamp, 
            :embedding_model, :error_message
        )
        """
        try:
            conn.execute(query, doc)
            logger.info(f"Inserted document metadata in SQLite registry: {doc['id']} ({doc['filename']})")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert document: {e}")
            raise DatabaseError(f"Database write failed: {e}") from e

    @staticmethod
    def get_document_by_hash(conn: sqlite3.Connection, file_hash: str) -> dict | None:
        query = "SELECT * FROM documents WHERE file_hash = ?"
        try:
            row = conn.execute(query, (file_hash,)).fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to query document by hash: {e}")
            raise DatabaseError(f"Database read failed: {e}") from e

    @staticmethod
    def get_document_by_id(conn: sqlite3.Connection, doc_id: str) -> dict | None:
        query = "SELECT * FROM documents WHERE id = ?"
        try:
            row = conn.execute(query, (doc_id,)).fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to query document by id: {e}")
            raise DatabaseError(f"Database read failed: {e}") from e

    @staticmethod
    def list_documents(conn: sqlite3.Connection, status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
        if status and status != "all":
            query = "SELECT * FROM documents WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (status, limit, offset)
        else:
            query = "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = (limit, offset)
            
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to list documents: {e}")
            raise DatabaseError(f"Database read failed: {e}") from e

    @staticmethod
    def count_documents(conn: sqlite3.Connection, status: str | None = None) -> int:
        if status and status != "all":
            query = "SELECT COUNT(*) FROM documents WHERE status = ?"
            params = (status,)
        else:
            query = "SELECT COUNT(*) FROM documents"
            params = ()
            
        try:
            count = conn.execute(query, params).fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(f"Failed to count documents: {e}")
            raise DatabaseError(f"Database count failed: {e}") from e

    @staticmethod
    def delete_document(conn: sqlite3.Connection, doc_id: str) -> None:
        query = "DELETE FROM documents WHERE id = ?"
        try:
            conn.execute(query, (doc_id,))
            logger.info(f"Deleted document from registry database: {doc_id}")
        except sqlite3.Error as e:
            logger.error(f"Failed to delete document: {e}")
            raise DatabaseError(f"Database delete failed: {e}") from e

    @staticmethod
    def update_document_status(conn: sqlite3.Connection, doc_id: str, status: str, chunk_count: int = 0, error_message: str = None) -> None:
        query = """
        UPDATE documents 
        SET status = ?, chunk_count = ?, error_message = ?, updated_at = ?
        WHERE id = ?
        """
        try:
            conn.execute(query, (status, chunk_count, error_message, datetime.utcnow().isoformat() + "Z", doc_id))
            logger.info(f"Updated status for document {doc_id} to {status} (chunks={chunk_count})")
        except sqlite3.Error as e:
            logger.error(f"Failed to update document status: {e}")
            raise DatabaseError(f"Database update failed: {e}") from e
