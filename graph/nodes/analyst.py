import json
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from graph.state import AgentState, Signal
from config import ANALYST_MODEL, PENSIONBOX_CONTEXT
semaphore = asyncio.Semaphore(10)
llm = ChatOpenAI(model=ANALYST_MODEL, temperature=0)

ANALYST_PROMPT = """
You are a senior competitive intelligence analyst for PensionBox.in.

{pensionbox_context}

Analyze this news item about a competitor and determine if it's strategically 
relevant to PensionBox. If it is, explain exactly what it means for PensionBox.

Article:
Competitor: {competitor}
Title: {title}
Content: {content}
URL: {url}

Respond ONLY with a JSON object:
{{
    "is_relevant": true or false,
    "signal_type": one of ["product_launch", "regulatory_response", "partnership", 
                           "hiring_signal", "pricing_change", "marketing_push", 
                           "market_news"] or "" if not relevant,
    "importance": "high", "medium", or "low" — based on threat/opportunity level,
    "summary": "2-3 sentence summary of what happened",
    "implication": "Specific implication for PensionBox — what should they know or do?",
    "citation": the exact URL
}}

Importance guide:
- high: direct threat or opportunity (competitor launching same product, 
        major partnership with HR platform PensionBox also targets,
        regulatory change PensionBox must respond to)
- medium: worth monitoring (competitor scaling team, new market push)
- low: background noise (general market commentary, minor updates)

If not relevant, return is_relevant: false and leave other fields empty.
Respond ONLY with JSON. No markdown, no preamble.
""".strip()


async def analyse_result(result: dict) -> dict | None:
 async with semaphore:
    prompt = ANALYST_PROMPT.format(
        pensionbox_context=PENSIONBOX_CONTEXT,
        competitor=result.get("competitor", ""),
        title=result.get("title", ""),
        content=result.get("content", "")[:1500],  # cap to save tokens
        url=result.get("url", "")
    )

    try:
        response = await llm.ainvoke(prompt)
        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        if not data.get("is_relevant"):
            return None

        return Signal(
            competitor=result.get("competitor", ""),
            title=result.get("title", ""),
            url=result.get("url", ""),
            summary=data.get("summary", ""),
            source=result.get("url", ""),
            signal_type=data.get("signal_type", ""),
            importance=data.get("importance", "low"),
            implication=data.get("implication", ""),
            published_at=result.get("published_date", "")
        )

    except json.JSONDecodeError:
        print(f"[analyst] JSON parse failed: {result.get('title')}")
        return None
    except Exception as e:
        print(f"[analyst] ERROR: {e}")
        return None


async def analyst_node(state: AgentState) -> dict:
    """
    Analyses all raw results concurrently.
    Filters to only relevant signals.
    """
    raw_results = state.get("raw_results", [])

    if not raw_results:
        print("[analyst] No raw results to analyse.")
        return {"signals": []}

    print(f"[analyst] Analysing {len(raw_results)} results...")

    # Run all concurrently
    tasks = [analyse_result(r) for r in raw_results]
    results = await asyncio.gather(*tasks)

    # Filter out None (irrelevant) results
    signals = [r for r in results if r is not None]

    # Sort by importance
    importance_order = {"high": 0, "medium": 1, "low": 2}
    signals.sort(key=lambda x: importance_order.get(x.get("importance", "low"), 2))

    print(f"[analyst] {len(raw_results)} results → {len(signals)} signals")
    return {"signals": signals}