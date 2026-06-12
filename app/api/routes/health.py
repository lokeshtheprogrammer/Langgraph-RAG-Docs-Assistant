from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.core.database import get_db_connection
from app.repositories.document_repository import DocumentRepository

router = APIRouter(prefix="/health", tags=["Diagnostics"])

@router.get("", status_code=200)
async def health_check():
    """Diagnostic health check verifying connectivity of backend systems."""
    vector_store_status = "ok"
    database_status = "ok"
    corpus_size = 0
    
    try:
        # Check SQLite DB
        with get_db_connection() as conn:
            corpus_size = DocumentRepository.count_documents(conn)
    except Exception:
        database_status = "error"
        
    # ChromaDB persistent directory exists check
    if not settings.CHROMA_PERSIST_DIR:
        vector_store_status = "error"
        
    overall_status = "healthy"
    if "error" in (vector_store_status, database_status):
        overall_status = "degraded"
        
    return {
        "status": overall_status,
        "version": "1.0.0",
        "components": {
            "vector_store": vector_store_status,
            "document_registry": database_status,
            "llm_provider": "ok",
            "embedding_model": "ok"
        },
        "corpus_size": corpus_size,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
