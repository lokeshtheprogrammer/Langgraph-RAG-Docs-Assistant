from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="The user's original query question")
    answer: str = Field(..., min_length=1, max_length=10000, description="The system's generated response")
    rating: Literal["thumbs_up", "thumbs_down"] = Field(..., description="Thumbs up or down rating")
    comment: str | None = Field(None, max_length=1000, description="Optional text comment")
    session_id: str | None = Field(None, description="UUID session correlation identifier")
    response_time_ms: int | None = Field(None, ge=0, description="Answer generation latency in ms")

class FeedbackResponse(BaseModel):
    feedback_id: str = Field(..., description="Assigned unique database feedback UUID")
    status: str = Field("recorded", description="Submit registration status")
    message: str = Field("Thank you for your feedback.", description="Response confirmation message")
