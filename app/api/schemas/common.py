from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable error explanation message")
    details: dict = Field(default_factory=dict, description="Detailed validation or contextual errors")

class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str = Field(..., description="Unique ID tracking the failed request")
