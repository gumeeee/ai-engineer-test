from tavily import TavilyClient

from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def run_web_search(query: str, max_results: int = 4) -> list[dict]:
    """Execute a web search using Tavily API.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of result dicts with keys: url, title, content.
    """
    client = TavilyClient(api_key=settings.tavily_api_key)
    logger.info("web_search.searching", query=query)
    response = client.search(query, max_results=max_results)
    results = response.get("results", [])
    logger.info("web_search.complete", count=len(results))
    return results
