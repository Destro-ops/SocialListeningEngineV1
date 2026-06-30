import asyncio
from datetime import timedelta, timezone, datetime
from tavily import AsyncTavilyClient
from graph.state import AgentState
from config import TAVILY_API_KEY

client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
CUTOFF_WEEKS = 1
CUTOFF = datetime.now(timezone.utc) - timedelta(weeks=CUTOFF_WEEKS)

def is_recent(result: dict) -> bool:
    pub_date = result.get("published_date")
    if not pub_date:
        return True  # no date info — let it through, or False to be strict
    try:
        parsed = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        return parsed >= CUTOFF
    except (ValueError, TypeError):
        return True

async def search_competitor(competitor: str, queries: list) -> list:
    """
    Run all queries for one competitor concurrently.
    Returns flat list of raw results tagged with competitor.
    """
    async def run_query(query: str) -> list:
        one_weeks_ago = (datetime.now(timezone.utc) - timedelta(weeks=1)).strftime("%Y-%m-%d")
        try:
            response = await client.search(
                query=query,
                max_results=5,
                search_depth="advanced",   # deeper search, worth the extra cost
                include_raw_content=False,
                time_range="year"  # summaries only, saves tokens
            )
            results = response.get("results", [])

            results = [r for r in results if is_recent(r)]

            # Tag each result with competitor + query that found it
            for r in results:
                r["competitor"] = competitor
                r["search_query"] = query

            print(f"[researcher] '{query}' → {len(results)} results")
            return results

        except Exception as e:
            print(f"[researcher] FAILED query '{query}': {e}")
            return []

    # Run all queries for this competitor concurrently
    tasks = [run_query(q) for q in queries]
    results = await asyncio.gather(*tasks)

    # Flatten
    return [r for batch in results for r in batch]


async def researcher_node(state: AgentState) -> dict:
    """
    Executes search plan from supervisor.
    Runs all competitors concurrently.
    """
    search_plan = state.get("search_plan", {})

    if not search_plan:
        print("[researcher] No search plan found. Skipping.")
        return {"raw_results": []}

    print(f"[researcher] Researching {len(search_plan)} competitors...")

    # Run all competitors concurrently
    tasks = [
        search_competitor(competitor, queries)
        for competitor, queries in search_plan.items()
    ]
    results = await asyncio.gather(*tasks)

    # Flatten all results
    all_results = [r for batch in results for r in batch]

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        if r.get("url") not in seen:
            seen.add(r["url"])
            unique.append(r)

    print(f"[researcher] {len(all_results)} results → {len(unique)} after dedup")
    return {"raw_results": unique}