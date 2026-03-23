import httpx

from app.config import settings

WIKIPEDIA_API = "https://fr.wikipedia.org/w/api.php"
BRAVE_API = "https://api.search.brave.com/res/v1/web/search"


async def search_external(query: str) -> list[dict[str, str]]:
    """Search Wikipedia and Brave for external context. Returns list of {title, snippet}."""
    results: list[dict[str, str]] = []

    headers = {"User-Agent": "MeetWise/1.0 (https://github.com/meetwise; contact@meetwise.app)"}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        # Wikipedia search
        wiki_results = await _search_wikipedia(client, query)
        results.extend(wiki_results)

        # Brave search (if API key configured)
        if settings.brave_api_key:
            brave_results = await _search_brave(client, query)
            results.extend(brave_results)

    return results[:5]


async def _search_wikipedia(client: httpx.AsyncClient, query: str) -> list[dict[str, str]]:
    """Search French Wikipedia for relevant articles."""
    results: list[dict[str, str]] = []
    try:
        resp = await client.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 3,
                "format": "json",
                "utf8": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("query", {}).get("search", []):
            results.append(
                {
                    "title": f"Wikipedia: {item['title']}",
                    "snippet": item.get("snippet", "")
                    .replace('<span class="searchmatch">', "")
                    .replace("</span>", ""),
                }
            )
    except httpx.HTTPError:
        pass
    return results


async def _search_brave(client: httpx.AsyncClient, query: str) -> list[dict[str, str]]:
    """Search Brave for relevant web results."""
    results: list[dict[str, str]] = []
    try:
        resp = await client.get(
            BRAVE_API,
            params={"q": query, "count": 3},
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": settings.brave_api_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("web", {}).get("results", []):
            results.append(
                {
                    "title": f"Web: {item.get('title', '')}",
                    "snippet": item.get("description", ""),
                }
            )
    except httpx.HTTPError:
        pass
    return results
