import httpx

from app.core.logging import logger
from app.infrastructure.web_search.base import WebSearchClientBase, WebSearchResult


class DuckDuckGoSearchClient(WebSearchClientBase):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def search(self, query: str, num_results: int = 5) -> list[WebSearchResult]:
        logger.info(f"DuckDuckGo web search: '{query}' (n={num_results})")
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        try:
            response = await self.client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            abstract = data.get("AbstractText", "")
            abstract_url = data.get("AbstractURL", "")

            if abstract:
                results.append(WebSearchResult(
                    title=data.get("AbstractSource", "DuckDuckGo"),
                    url=abstract_url,
                    snippet=abstract[:500],
                    content=abstract
                ))

            related = data.get("RelatedTopics", [])
            for topic in related:
                if len(results) >= num_results:
                    break
                if "Text" in topic and "FirstURL" in topic:
                    results.append(WebSearchResult(
                        title=topic.get("Text", "")[:100],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", "")[:500]
                    ))

            # If API returned nothing, fall back to HTML scraping
            if not results:
                results = await self._scrape_html(query, num_results)

            logger.info(f"DuckDuckGo returned {len(results)} results.")
            return results[:num_results]

        except Exception as e:
            logger.warning(f"DuckDuckGo API search failed: {e}. Trying HTML fallback.")
            try:
                return await self._scrape_html(query, num_results)
            except Exception as e2:
                logger.error(f"DuckDuckGo HTML fallback also failed: {e2}")
                return []

    async def _scrape_html(self, query: str, num_results: int) -> list[WebSearchResult]:
        logger.info("DuckDuckGo HTML fallback search...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = await self.client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=headers
        )
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result in soup.select(".result")[:num_results]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")

            if title_el:
                results.append(WebSearchResult(
                    title=title_el.get_text(strip=True)[:100],
                    url=title_el.get("href", ""),
                    snippet=snippet_el.get_text(strip=True)[:500] if snippet_el else ""
                ))

        return results

    async def close(self):
        await self.client.aclose()
