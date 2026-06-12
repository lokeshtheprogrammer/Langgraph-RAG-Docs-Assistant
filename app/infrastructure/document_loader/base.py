from abc import ABC, abstractmethod


class DocumentLoaderBase(ABC):
    """Abstract Base Class defining the document loader adapter contract."""

    @abstractmethod
    def load(self, source: str) -> str:
        """Load document content and return raw text string."""
        pass
