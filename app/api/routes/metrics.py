from fastapi import APIRouter

from app.core.database import get_db_connection
from app.core.logging import logger

router = APIRouter(tags=["Metrics"])

@router.get("/metrics")
async def get_metrics():
    """Return system-wide statistics for monitoring and evaluation."""
    logger.info("Fetching system metrics...")
    
    with get_db_connection() as conn:
        # Document statistics
        doc_row = conn.execute("SELECT COUNT(*) as total, COALESCE(SUM(chunk_count), 0) as chunks FROM documents WHERE status = 'indexed'").fetchone()
        total_documents = doc_row["total"]
        total_chunks = doc_row["chunks"]
        
        # Feedback statistics
        fb_row = conn.execute("SELECT COUNT(*) as total FROM feedback").fetchone()
        total_feedback = fb_row["total"]
        
        pos_row = conn.execute("SELECT COUNT(*) as total FROM feedback WHERE rating = 'thumbs_up'").fetchone()
        feedback_positive = pos_row["total"]
        
        neg_row = conn.execute("SELECT COUNT(*) as total FROM feedback WHERE rating = 'thumbs_down'").fetchone()
        feedback_negative = neg_row["total"]
        
        # Average response time
        avg_row = conn.execute("SELECT AVG(response_time_ms) as avg_ms FROM feedback WHERE response_time_ms IS NOT NULL").fetchone()
        avg_response_time = round(avg_row["avg_ms"], 1) if avg_row["avg_ms"] else 0
        
        # Conversation sessions
        session_row = conn.execute("SELECT COUNT(DISTINCT session_id) as total FROM chat_history").fetchone()
        total_sessions = session_row["total"]
    
    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "total_feedback": total_feedback,
        "feedback_positive": feedback_positive,
        "feedback_negative": feedback_negative,
        "average_response_time_ms": avg_response_time,
        "total_sessions": total_sessions
    }
