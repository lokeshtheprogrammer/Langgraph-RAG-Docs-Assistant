from abc import ABC, abstractmethod


class LLMClientBase(ABC):
    """Abstract Base Class defining the LLM provider adapter contract."""

    @abstractmethod
    async def ainvoke(self, messages: list[dict], **kwargs) -> str:
        """Asynchronously invoke the LLM with a list of chat messages."""
        pass
