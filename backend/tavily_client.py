"""
backend/tavily_client.py
Thin wrapper around the Tavily search API. Used exclusively by the
Domain Specialist agent (backend/agents/domain_specialist.py) to research
the likely domain of an uploaded dataset before any other agent runs.
"""
from tavily import TavilyClient

from backend.config import settings

_client: TavilyClient | None = None


def _get_client() -> TavilyClient | None:
    global _client
    if not settings.TAVILY_API_KEY:
        return None
    if _client is None:
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


def tavily_search(query: str, max_results: int = 4) -> str:
    """Runs a search and returns a compact text digest of the top results.
    Degrades gracefully (returns a placeholder string) if TAVILY_API_KEY is
    not configured or the search fails, so a missing/broken search
    integration never crashes the upload flow — the domain brief will
    just be less specific."""
    client = _get_client()
    if client is None:
        return "(Tavily not configured — no web research available for this query)"
    try:
        result = client.search(query=query, max_results=max_results, search_depth="basic")
    except Exception as e:
        return f"(search failed for '{query}': {e})"

    snippets = []
    for r in result.get("results", []):
        title = r.get("title", "")
        content = r.get("content", "")[:500]
        snippets.append(f"- {title}: {content}")
    return "\n".join(snippets) if snippets else "(no results)"
