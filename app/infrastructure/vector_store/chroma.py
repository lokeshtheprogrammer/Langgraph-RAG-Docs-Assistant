import chromadb

from app.core.exceptions import VectorStoreError
from app.core.logging import logger
from app.infrastructure.vector_store.base import VectorStoreBase
from app.workflow.state import DocumentChunk


class ChromaVectorStore(VectorStoreBase):
    """Persistent ChromaDB implementation of the vector store."""

    def __init__(self, persist_dir: str):
        logger.info(f"Initializing persistent ChromaDB client at: {persist_dir}...")
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="technical_docs",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB persistent client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise VectorStoreError(f"ChromaDB initialization failed: {e}")

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]:
        if not chunks:
            return []
        
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # Construct a clean chunk ID
            chunk_id = f"chunk_{chunk.document_id}_{chunk.chunk_index}"
            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append({
                "document_id": chunk.document_id,
                "source_file": chunk.source_file,
                "chunk_index": chunk.chunk_index
            })
            
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(chunks)} chunks to ChromaDB.")
            return ids
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            raise VectorStoreError(f"Failed to write vectors: {e}") from e

    def similarity_search_by_vector(self, vector: list[float], k: int = 5) -> list[DocumentChunk]:
        try:
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            chunks = []
            if not results or not results["ids"] or not results["ids"][0]:
                return chunks
                
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if results.get("distances") else [None] * len(ids)
            
            for i in range(len(ids)):
                meta = metadatas[i]
                chunks.append(DocumentChunk(
                    content=documents[i],
                    source_file=meta.get("source_file", "unknown"),
                    document_id=meta.get("document_id", "unknown"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    distance=float(distances[i]) if distances[i] is not None else None
                ))
            return chunks
        except Exception as e:
            logger.error(f"ChromaDB query similarity search failed: {e}")
            raise VectorStoreError(f"Vector search query failed: {e}") from e

    def delete_by_document_id(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted all vector chunks for document_id: {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document vectors from ChromaDB: {e}")
            raise VectorStoreError(f"Vector deletion failed: {e}") from e
