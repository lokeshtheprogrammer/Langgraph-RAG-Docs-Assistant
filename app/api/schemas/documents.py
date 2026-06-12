
from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    document_id: str = Field(..., alias="id", description="Assigned unique document ID")
    filename: str = Field(..., description="Document filename")
    source_url: str = Field(..., description="Source remote URL scrape location")
    chunk_count: int = Field(..., description="Number of vector chunks generated")
    file_type: str = Field(..., description="File format extension")
    status: str = Field(..., description="Catalog registration status")
    ingestion_timestamp: str = Field(..., description="ISO8601 creation timestamp")
    file_size_bytes: int = Field(..., description="File size in bytes")

    class Config:
        populate_by_name = True

class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord] = Field(..., description="List of registered documents")
    total: int = Field(..., description="Total documents matching filter count")
    limit: int = Field(..., description="Maximum records limit returned")
    offset: int = Field(..., description="Pagination offset index")
