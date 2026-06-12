
from app.config import settings
from app.core.logging import logger
from app.infrastructure.web_search.base import WebSearchClientBase
from app.infrastructure.web_search.duckduckgo import DuckDuckGoSearchClient
from app.infrastructure.web_search.tavily import TavilySearchClient

_web_search_client: WebSearchClientBase | None = None

def get_web_search_client() -> WebSearchClientBase | None:
    global _web_search_client
    if _web_search_client is not None:
        return _web_search_client

    if not settings.WEB_SEARCH_ENABLED:
        logger.info("Web search is disabled via configuration.")
        return None

    provider = settings.WEB_SEARCH_PROVIDER.lower()
    logger.info(f"Initializing web search client: {provider}")

    if provider == "tavily":
        _web_search_client = TavilySearchClient(settings.TAVILY_API_KEY)
    elif provider == "duckduckgo":
        _web_search_client = DuckDuckGoSearchClient()
    else:
        logger.warning(f"Unknown web search provider '{provider}'. Falling back to DuckDuckGo.")
        _web_search_client = DuckDuckGoSearchClient()

    return _web_search_client
