from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    document_id: str = Field(..., description="Assigned unique document ID")
    filename: str = Field(..., description="Original filename or URL filename")
    chunks_indexed: int = Field(..., description="Number of vector chunks successfully indexed")
    file_size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Catalog index status")
    message: str = Field(..., description="Human-readable result summary message")
    duplicate: bool = Field(..., description="True if document content was already indexed")
