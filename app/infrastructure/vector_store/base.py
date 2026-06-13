from abc import ABC, abstractmethod

from app.workflow.state import DocumentChunk


class VectorStoreBase(ABC):
    """Abstract Base Class defining the vector store adapter contract."""

    @abstractmethod
    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]:
        """Add document chunks and their embeddings to the vector store."""
        pass

    @abstractmethod
    def similarity_search_by_vector(
        self, vector: list[float], k: int = 5, where_filter: dict | None = None
    ) -> list[DocumentChunk]:
        """Perform similarity search using a query vector."""
        pass

    @abstractmethod
    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks belonging to a specific document ID."""
        pass

    @abstractmethod
    def get_all_chunks(self, where_filter: dict | None = None) -> list[DocumentChunk]:
        """Retrieve all document chunks, optionally filtered by metadata."""
        pass

