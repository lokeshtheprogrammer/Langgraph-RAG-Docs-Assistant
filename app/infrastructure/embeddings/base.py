from abc import ABC, abstractmethod


class EmbeddingModelBase(ABC):
    """Abstract Base Class defining the embedding model adapter contract."""
    
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings into vectors."""
        pass
        
    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a vector."""
        pass
