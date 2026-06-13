import asyncio
import glob
import os

from app.config import settings
from app.core.database import initialize_db
from app.core.logging import logger
from app.infrastructure.embeddings.sentence_transformers import SentenceTransformerAdapter
from app.infrastructure.vector_store.chroma import ChromaVectorStore
from app.services.ingestion_service import IngestionService


async def main():
    logger.info("Starting document corpus ingestion script...")
    
    # Idempotent DB initialization
    initialize_db()
    
    # Initialize adapters
    embedding_model = SentenceTransformerAdapter(settings.EMBEDDING_MODEL)
    vector_store = ChromaVectorStore(settings.CHROMA_PERSIST_DIR)
    
    # Initialize service
    ingestion_service = IngestionService(vector_store, embedding_model)
    
    # Locate all markdown files in corpus directory
    corpus_pattern = os.path.join("corpus", "*.md")
    files = glob.glob(corpus_pattern)
    
    if not files:
        logger.warning("No document markdown files found in 'corpus/' directory to ingest.")
        return
        
    logger.info(f"Found {len(files)} files in 'corpus/'. Starting ingestion processing...")
    
    success_count = 0
    duplicate_count = 0
    failed_count = 0
    
    for filepath in files:
        try:
            result = await ingestion_service.ingest_file(filepath)
            if result.get("duplicate"):
                duplicate_count += 1
            else:
                success_count += 1
            print(f"Processed: {filepath} -> Status: {result['status']} (Chunks: {result['chunks_indexed']}, Duplicate: {result['duplicate']})")
        except Exception as e:
            failed_count += 1
            print(f"FAILED to ingest: {filepath} -> Error: {e}")
            
    logger.info(f"Ingestion process finished. Results: Success={success_count}, Duplicate={duplicate_count}, Failed={failed_count}")

if __name__ == "__main__":
    asyncio.run(main())
