import datetime
import uuid
import datetime
from typing import Optional
from app.api.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.core.database import get_db_connection
from app.core.logging import logger
from app.repositories.feedback_repository import FeedbackRepository


class FeedbackService:
    """Orchestrates feedback persistence logic using SQLite database."""

    async def submit_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        feedback_id = f"fb_{uuid.uuid4()}"
        created_at = datetime.datetime.utcnow().isoformat() + "Z"
        
        feedback_record = {
            "feedback_id": feedback_id,
            "query": request.query,
            "answer": request.answer,
            "rating": request.rating,
            "comment": request.comment,
            "sources_used": None, # Handled in DB JSON parse if populated later
            "session_id": request.session_id,
            "query_type": None, # Will populate dynamically if present
            "retry_count": 0,
            "response_time_ms": request.response_time_ms,
            "created_at": created_at
        }
        
        logger.info(f"Submitting user feedback rating={request.rating}...")
        
        with get_db_connection() as conn:
            FeedbackRepository.insert_feedback(conn, feedback_record)
            
        return FeedbackResponse(
            feedback_id=feedback_id,
            status="recorded",
            message="Thank you for your feedback."
        )

    async def list_feedbacks(self, rating: Optional[str] = None, limit: int = 50, offset: int = 0) -> dict:
        with get_db_connection() as conn:
            items = FeedbackRepository.list_feedback(conn, rating, limit, offset)
            total = FeedbackRepository.count_feedback(conn, rating)
            return {
                "feedback": items,
                "total": total,
                "limit": limit,
                "offset": offset
            }
