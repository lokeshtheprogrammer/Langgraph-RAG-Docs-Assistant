
import httpx

from app.core.logging import logger
from app.infrastructure.web_search.base import WebSearchClientBase, WebSearchResult


class TavilySearchClient(WebSearchClientBase):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=15.0)

    async def search(self, query: str, num_results: int = 5) -> list[WebSearchResult]:
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not configured. Tavily search unavailable.")
            return []

        logger.info(f"Tavily web search: '{query}' (n={num_results})")
        try:
            response = await self.client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": num_results,
                    "include_answer": False
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for r in data.get("results", []):
                results.append(WebSearchResult(
                    title=r.get("title", "")[:100],
                    url=r.get("url", ""),
                    snippet=r.get("content", "")[:500],
                    content=r.get("content", "")
                ))

            logger.info(f"Tavily returned {len(results)} results.")
            return results

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    async def close(self):
        await self.client.aclose()
