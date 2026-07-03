import json
import asyncio
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from graph.state import AgentState, Signal
from config import ANALYST_MODEL, PENSIONBOX_CONTEXT, SUBREDDITS
semaphore = asyncio.Semaphore(10)
llm = ChatOpenAI(model=ANALYST_MODEL, temperature=0.2)

COMPETITOR_ANALYST_PROMPT = """
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

COMMUNITY_ANALYST_PROMPT = """
You are a community insights analyst for PensionBox.in.

{pensionbox_context}

Analyze this Reddit/Quora/Twitter post and determine if it's a relevant signal 
about corporate NPS, EPF, NPS vatsalya EPF, employee benefits, SIP's(systematic investment plan), FD(fixed deposit), PPF(provident pension fund), taxes or PensionBox specifically.
Also get news on retirement plans, pension schemes, and other related topics. If it is relevant, explain exactly what it means for PensionBox.
NOTE: If the post is spam, unrelated, or about a different country's pension system, mark it as not relevant.
also do not get news about income tax (IT).
Post:
Topic searched: {competitor}
Title: {title}
Content: {content}
URL: {url}

Respond ONLY with a JSON object:
{{
    "is_relevant": true or false,
    "signal_type": one of ["pain_point", "comparison_question", "positive_mention", 
                           "negative_mention", "general_question", "competitor_mention"] 
                           or "" if not relevant,
    "importance": "high", "medium", or "low" — high if PensionBox is mentioned directly 
                  or it's a widely-engaged thread, medium if relevant topic with no brand 
                  mention, low if tangential,
    "summary": "2-3 sentence summary of what the person is saying/asking",
    "implication": "What should PensionBox do — respond, monitor, use as content idea, etc?",
    "sentiment": "positive", "negative", or "neutral",
    "mentions_pensionbox": true or false,
    "citation": the exact URL
}}

If not relevant (spam, unrelated content, different country's pension system), 
return is_relevant: false and leave other fields empty.
Respond ONLY with JSON. No markdown, no preamble.
""".strip()


async def analyse_result(result: dict) -> dict | None:
    async with semaphore:
        is_community = result.get("source_type") == "community"
        prompt_template = COMMUNITY_ANALYST_PROMPT if is_community else COMPETITOR_ANALYST_PROMPT

        prompt = prompt_template.format(
            pensionbox_context=PENSIONBOX_CONTEXT,
            competitor=result.get("competitor") or result.get("topic", ""),
            title=result.get("title", ""),
            content=result.get("content", "")[:1500],
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
                published_at=result.get("published_date", ""),
                source_type=result.get("source_type", "competitor"),
                sentiment=data.get("sentiment"),
                mentions_pensionbox=data.get("mentions_pensionbox")
            )

        except json.JSONDecodeError:
            print(f"[analyst] JSON parse failed: {result.get('title')}")
            return None
        except Exception as e:
            print(f"[analyst] ERROR: {e}")
            return None


async def analyst_node(state: AgentState) -> dict:
    """
    Analyses raw_results (competitor mode) or community_results (community mode)
    concurrently. Filters to only relevant signals.
    """
    raw_results = state.get("raw_results", [])
    community_results = state.get("community_results", [])
    items = raw_results + community_results

    if not items:
        print("[analyst] No results to analyse.")
        return {"signals": []}

    print(f"[analyst] Analysing {len(items)} results...")

    tasks = [analyse_result(r) for r in items]
    results = await asyncio.gather(*tasks)

    signals = [r for r in results if r is not None]

    importance_order = {"high": 0, "medium": 1, "low": 2}
    signals.sort(key=lambda x: importance_order.get(x.get("importance", "low"), 2))

    print(f"[analyst] {len(items)} results → {len(signals)} signals")
    return {"signals": signals}