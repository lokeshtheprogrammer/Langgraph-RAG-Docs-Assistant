import datetime
import os

from app.config import settings
from app.core.database import get_db_connection
from app.core.exceptions import IngestionError
from app.core.logging import logger
from app.infrastructure.document_loader.file_loader import LocalFileLoader
from app.infrastructure.document_loader.url_loader import UrlDocumentLoader
from app.infrastructure.embeddings.sentence_transformers import SentenceTransformerAdapter
from app.infrastructure.vector_store.chroma import ChromaVectorStore
from app.repositories.document_repository import DocumentRepository
from app.utils.chunking import split_text
from app.utils.hashing import calculate_sha256, calculate_sha256_string
from app.workflow.state import DocumentChunk


class IngestionService:
    """Orchestrates document loading, text splitting, embedding, vector storage, and SQLite registry."""

    def __init__(self, vector_store: ChromaVectorStore, embedding_model: SentenceTransformerAdapter):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.file_loader = LocalFileLoader()
        self.url_loader = UrlDocumentLoader()

    async def ingest_file(self, filepath: str) -> dict:
        """Ingests a local document file into the vector store and registry."""
        filename = os.path.basename(filepath)
        logger.info(f"Initiating ingestion for file: {filename}")
        
        try:
            with open(filepath, "rb") as f:
                content_bytes = f.read()
            file_size = len(content_bytes)
            file_hash = calculate_sha256(content_bytes)
        except Exception as e:
            logger.error(f"Failed to read file bytes: {e}")
            raise IngestionError(f"Could not read source file bytes: {e}") from e
            
        return await self._ingest(
            source_path=filepath,
            filename=filename,
            source_url="",
            file_hash=file_hash,
            file_size_bytes=file_size,
            file_type=os.path.splitext(filename)[1].lstrip("."),
            is_url=False
        )

    async def ingest_url(self, url: str) -> dict:
        """Ingests a remote web document URL into the vector store and registry."""
        logger.info(f"Initiating ingestion for URL: {url}")
        
        # Derived values for catalog registry
        file_hash = calculate_sha256_string(url)
        filename = url.split("/")[-1] or "webpage.html"
        if not filename.endswith((".html", ".htm")):
            filename += ".html"
            
        return await self._ingest(
            source_path=url,
            filename=filename,
            source_url=url,
            file_hash=file_hash,
            file_size_bytes=0, # Unknown until fetch, set to 0 for url
            file_type="html",
            is_url=True
        )

    async def _ingest(self, source_path: str, filename: str, source_url: str, 
                      file_hash: str, file_size_bytes: int, file_type: str, is_url: bool) -> dict:
                      
        # Step 1: Duplicate check via SQLite registry
        with get_db_connection() as conn:
            existing = DocumentRepository.get_document_by_hash(conn, file_hash)
            if existing:
                logger.info(f"Document duplicate detected: {filename} has already been indexed (hash: {file_hash})")
                return {
                    "document_id": existing["id"],
                    "filename": existing["filename"],
                    "chunks_indexed": 0,
                    "file_size_bytes": existing["file_size_bytes"],
                    "status": existing["status"],
                    "message": "Document already indexed.",
                    "duplicate": True
                }

        # Step 2: Create a unique document ID
        document_id = f"doc_{file_hash[:8]}"
        ingestion_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Initialize processing metadata in SQLite database
        doc_record = {
            "id": document_id,
            "filename": filename,
            "source_url": source_url,
            "file_hash": file_hash,
            "file_size_bytes": file_size_bytes,
            "file_type": file_type,
            "chunk_count": 0,
            "status": "processing",
            "ingestion_timestamp": ingestion_timestamp,
            "embedding_model": settings.EMBEDDING_MODEL,
            "error_message": None
        }
        
        with get_db_connection() as conn:
            DocumentRepository.insert_document(conn, doc_record)

        try:
            # Step 3: Load raw text content
            if is_url:
                raw_text = self.url_loader.load(source_path)
                # Update file size bytes dynamically based on content length
                file_size_bytes = len(raw_text.encode("utf-8"))
            else:
                raw_text = self.file_loader.load(source_path)
                
            if not raw_text.strip():
                raise IngestionError("Document has no extractable text content.")
                
            # Step 4: Chunk document text
            text_chunks = split_text(raw_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            chunk_count = len(text_chunks)
            
            # Step 5: Embed chunks and save to ChromaDB
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    source_file=filename,
                    document_id=document_id,
                    chunk_index=i
                ))
                
            embeddings = self.embedding_model.embed_documents(text_chunks)
            self.vector_store.add_chunks(chunks, embeddings)
            
            # Step 6: Mark success status in SQLite
            with get_db_connection() as conn:
                DocumentRepository.update_document_status(
                    conn=conn,
                    doc_id=document_id,
                    status="indexed",
                    chunk_count=chunk_count
                )
                
            logger.info(f"Ingestion successful for {filename}. Indexed {chunk_count} chunks.")
            return {
                "document_id": document_id,
                "filename": filename,
                "chunks_indexed": chunk_count,
                "file_size_bytes": file_size_bytes,
                "status": "indexed",
                "message": f"Document '{filename}' successfully indexed with {chunk_count} chunks.",
                "duplicate": False
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to ingest document {filename}: {error_msg}")
            
            # Update registry status to failed
            try:
                with get_db_connection() as conn:
                    DocumentRepository.update_document_status(
                        conn=conn,
                        doc_id=document_id,
                        status="failed",
                        chunk_count=0,
                        error_message=error_msg
                    )
            except Exception as dbe:
                logger.error(f"Double fault: failed to update registry state: {dbe}")
                
            raise IngestionError(f"Ingestion failed: {error_msg}") from e

    async def delete_document(self, document_id: str) -> int:
        """Deletes a document from the SQLite registry and its associated vector chunks from ChromaDB."""
        logger.info(f"Attempting to delete document: {document_id}")
        
        with get_db_connection() as conn:
            existing = DocumentRepository.get_document_by_id(conn, document_id)
            if not existing:
                logger.error(f"Delete failed: document {document_id} not found in registry database.")
                raise IngestionError(f"Document '{document_id}' not found.")
                
            chunk_count = existing["chunk_count"]
            
        # Delete vectors
        self.vector_store.delete_by_document_id(document_id)
        
        # Delete catalog meta
        with get_db_connection() as conn:
            DocumentRepository.delete_document(conn, document_id)
            
        logger.info(f"Successfully deleted document {document_id} and its {chunk_count} vector chunks.")
        return chunk_count
