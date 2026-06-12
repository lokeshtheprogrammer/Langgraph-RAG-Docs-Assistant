from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.documents import DocumentListResponse, DocumentRecord
from app.core.database import get_db_connection
from app.dependencies import get_ingestion_service
from app.repositories.document_repository import DocumentRepository
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["Catalog"])

@router.get("", response_model=DocumentListResponse)
async def list_indexed_documents(
    status: str = Query("all", description="Filter by index status: indexed, failed, processing, all"),
    limit: int = Query(50, ge=1, le=100, description="Page limit size"),
    offset: int = Query(0, ge=0, description="Offset index"),
):
    """Retrieve a paginated catalog list of all documents registered in the system."""
    with get_db_connection() as conn:
        items = DocumentRepository.list_documents(conn, status, limit, offset)
        total = DocumentRepository.count_documents(conn, status)
        
    records = [DocumentRecord(**item) for item in items]
    return DocumentListResponse(
        documents=records,
        total=total,
        limit=limit,
        offset=offset
    )

@router.delete("/{document_id}", status_code=200)
async def delete_indexed_document(
    document_id: str,
    service: IngestionService = Depends(get_ingestion_service)
):
    """Remove a document's registration and clean its vector embeddings chunks from the store."""
    try:
        chunks_deleted = await service.delete_document(document_id)
        return {
            "document_id": document_id,
            "chunks_removed": chunks_deleted,
            "status": "deleted",
            "message": f"Document '{document_id}' and {chunks_deleted} vector chunks have been removed."
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
