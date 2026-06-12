from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class WebSearchResult(BaseModel):
    title: str = Field(..., description="Search result title")
    url: str = Field(..., description="Source URL")
    snippet: str = Field(..., description="Text snippet from the result")
    content: str | None = Field(None, description="Full extracted content if available")

class WebSearchClientBase(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> list[WebSearchResult]:
        pass
