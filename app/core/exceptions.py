class RAGError(Exception):
    """Base exception for all RAG system failures."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class LLMProviderError(RAGError):
    """Raised when an external LLM API request fails or times out."""
    pass

class VectorStoreError(RAGError):
    """Raised when ChromaDB operations fail."""
    pass

class DatabaseError(RAGError):
    """Raised when SQLite registry or feedback store operations fail."""
    pass

class IngestionError(RAGError):
    """Raised when document parsing, loading, or chunking splits fail."""
    pass

class ValidationError(RAGError):
    """Raised when request payload parameters violate constraints."""
    pass

