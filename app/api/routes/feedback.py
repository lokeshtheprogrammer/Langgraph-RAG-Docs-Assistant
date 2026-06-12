from fastapi import APIRouter, Depends, Query

from app.api.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.dependencies import get_feedback_service
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("", response_model=FeedbackResponse)
async def submit_user_feedback(
    request: FeedbackRequest,
    service: FeedbackService = Depends(get_feedback_service)
) -> FeedbackResponse:
    """Record user feedback (thumbs up/down and text comments) for generated answers."""
    return await service.submit_feedback(request)

@router.get("")
async def list_feedback_records(
    rating: str = Query("all", description="Filter by rating: thumbs_up, thumbs_down, all"),
    limit: int = Query(50, ge=1, le=100, description="Page limit size"),
    offset: int = Query(0, ge=0, description="Offset index"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """Retrieve logged user feedback records for review and offline quality assessment."""
    return await service.list_feedbacks(rating, limit, offset)
