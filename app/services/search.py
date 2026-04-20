"""
Web search service using DuckDuckGo for market data collection.

Searches for current trade opportunities, market analysis, and
industry news for a given sector in India.
"""

import logging
from dataclasses import dataclass

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str


def search_market_data(sector: str, max_results_per_query: int = 5) -> tuple[list[SearchResult], str]:
    """
    Search for market data related to the given sector in India.

    Returns:
        tuple: (list of SearchResult objects, aggregated text context for AI analysis)
    """
    queries = [
        f"{sector} India trade opportunities 2026",
        f"{sector} India market analysis export import",
        f"{sector} India industry news trends government policy",
    ]

    all_results: list[SearchResult] = []
    seen_urls: set[str] = set()

    with DDGS() as ddgs:
        for query in queries:
            try:
                logger.info(f"Searching: {query}")
                results = ddgs.text(
                    query,
                    max_results=max_results_per_query,
                    region="in-en",  # India - English
                )

                for r in results:
                    url = r.get("href", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    all_results.append(SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", ""),
                    ))

            except Exception as e:
                logger.warning(f"Search query failed: {query} — {e}")
                continue

    if not all_results:
        logger.warning(f"No search results found for sector: {sector}")
        return [], ""

    # Build aggregated text context for AI
    context_parts = []
    for i, result in enumerate(all_results, 1):
        context_parts.append(
            f"[Source {i}] {result.title}\n"
            f"URL: {result.url}\n"
            f"Summary: {result.snippet}\n"
        )

    aggregated_context = "\n".join(context_parts)
    logger.info(f"Collected {len(all_results)} unique results for sector: {sector}")

    return all_results, aggregated_context
