import asyncio
import json
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from config import RESEARCH_MODEL

llm = ChatOpenAI(model=RESEARCH_MODEL, temperature=0)

DEDUP_PROMPT = """
You are given a list of news signals. Group signals that cover the SAME 
underlying story or event.

Return ONLY a JSON array of clusters. Each cluster is a list of signal indices.
Example: [[0,3,7], [1,2], [4], [5,6,8]]

Rules:
- Same story = same event, same announcement, same regulatory change
- Different outlets covering same news = same cluster
- Genuinely different stories = separate clusters
- Return ONLY the JSON array, nothing else

Signals:
{signals}
""".strip()


async def dedup_node(state: AgentState) -> dict:
    """
    Clusters signals covering the same story.
    Keeps one representative per cluster — the most detailed one.
    """
    signals = state.get("signals", [])

    if len(signals) <= 1:
        return {"signals": signals}
    if len(signals) > 50:
        signals = signals[:50]
        print(f"[dedup] Capped at 50 signals to avoid rate limit")

    print(f"[dedup] Clustering {len(signals)} signals...")

    # Build numbered list of titles for LLM
    titles_block = "\n".join(
        f"{i}. [{s['competitor']}] {s['title']}"
        for i, s in enumerate(signals)
    )

    try:
        response = await llm.ainvoke(
            DEDUP_PROMPT.format(signals=titles_block)
        )
        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        clusters = json.loads(raw)

        deduped = []
        for cluster in clusters:
            if not cluster:
                continue

            members = [signals[i] for i in cluster if i < len(signals)]

            # Pick the one with the most detailed implication
            best = max(members, key=lambda x: len(x.get("implication", "")))

            # Preserve all source URLs for citation
            best["also_covered_by"] = [
                m["url"] for m in members
                if m["url"] != best["url"]
            ]

            deduped.append(best)

        print(f"[dedup] {len(signals)} signals → {len(deduped)} unique stories")
        return {"signals": deduped}

    except Exception as e:
        print(f"[dedup] Failed: {e} — returning undeduped")
        return {"signals": signals}