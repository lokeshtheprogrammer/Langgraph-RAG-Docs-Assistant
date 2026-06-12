class RAGException(Exception):
    """Base exception for all RAG system failures."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class LLMProviderError(RAGException):
    """Raised when an external LLM API request fails or times out."""
    pass

class VectorStoreError(RAGException):
    """Raised when ChromaDB operations fail."""
    pass

class DatabaseError(RAGException):
    """Raised when SQLite registry or feedback store operations fail."""
    pass

class IngestionError(RAGException):
    """Raised when document parsing, loading, or chunking splits fail."""
    pass

class ValidationError(RAGException):
    """Raised when request payload parameters violate constraints."""
    pass
