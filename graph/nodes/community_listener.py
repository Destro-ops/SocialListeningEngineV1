import asyncio
from datetime import timedelta, timezone, datetime
from tavily import AsyncTavilyClient
from graph.state import AgentState
from config import TAVILY_API_KEY, COMMUNITY_TOPICS, COMMUNITY_SOURCES

client = AsyncTavilyClient(api_key=TAVILY_API_KEY)


async def search_topic(topic: str, source: str) -> list:
    query = f"{source} {topic}"
    try:
        response = await client.search(
            query=query,
            max_results=5,
            search_depth="basic",   # cheaper than researcher.py's "advanced" — community noise doesn't need deep crawl
            include_raw_content=False,
            time_range="month"      # community chatter goes stale fast vs. competitor news
        )
        results = response.get("results", [])

        for r in results:
            r["source_type"] = "community"
            r["topic"] = topic
            r["search_query"] = query

        print(f"[community_listener] '{query}' → {len(results)} results")
        return results

    except Exception as e:
        print(f"[community_listener] FAILED query '{query}': {e}")
        return []


async def community_listener_node(state: AgentState) -> dict:
    """
    Searches Reddit/Quora/Twitter via Tavily for organic conversation
    about corporate NPS / EPF / PensionBox. Runs in place of researcher_node
    when state["mode"] == "community".
    """
    print(f"[community_listener] Searching {len(COMMUNITY_TOPICS)} topics × {len(COMMUNITY_SOURCES)} sources...")

    tasks = [
        search_topic(topic, source)
        for topic in COMMUNITY_TOPICS
        for source in COMMUNITY_SOURCES
    ]
    results = await asyncio.gather(*tasks)
    all_results = [r for batch in results for r in batch]

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        if r.get("url") not in seen:
            seen.add(r["url"])
            unique.append(r)

    print(f"[community_listener] {len(all_results)} results → {len(unique)} after dedup")
    return {"community_results": unique}