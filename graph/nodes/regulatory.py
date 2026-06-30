import asyncio
import json
import re
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from tavily import AsyncTavilyClient
from langchain_openai import ChatOpenAI
from config import TAVILY_API_KEY, REGULATORY_MODEL, PENSIONBOX_CONTEXT

search_client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
llm = ChatOpenAI(model=REGULATORY_MODEL, temperature=0.1)  # slight creativity for summarisation

# We monitor this ONE page directly instead of running broad Tavily text
# searches across the whole web. PFRDA's press releases page lists every
# release with a clean title + "**Issue Date:** DD-MM-YYYY" + URL, all
# inside one markdown link block per entry:
#
#   [## Title text here
#   **Issue Date:** 22-06-2026](https://www.pfrda.org.in/w/actual-slug?...)
#
# Verified against real Tavily extract() output for this page on 2026-06-24.
# No PDF parsing, no filename-date guessing, no relevance/staleness
# classification needed — if it's on this page, it's a real press release.
PFRDA_PRESS_RELEASES_URL = "https://www.pfrda.org.in/media/press-releases"

ENTRY_PATTERN = re.compile(
    r"\[##\s*(?P<title>.+?)\s*\n\s*\*\*Issue Date:\*\*\s*"
    r"(?P<day>\d{2})-(?P<month>\d{2})-(?P<year>\d{4})\]"
    r"\((?P<url>https?://[^\s)]+)\)",
    re.DOTALL,
)

SUMMARY_PROMPT = """
You are a regulatory analyst for PensionBox.in — an Indian B2B fintech helping SMEs manage corporate NPS, EPF, and employee benefits.

{pensionbox_context}

You are given the title and page content of a PFRDA press release. Summarize it and give PensionBox-specific context.

Respond ONLY with this JSON:
{{
    "summary": "2-3 sentence summary of what PFRDA announced",
    "implication": "one sharp sentence on what this means for PensionBox specifically. If there genuinely is no meaningful implication for PensionBox, say so plainly rather than forcing one.",
    "importance": "high", "medium", or "low"
}}

High importance: new NPS rules, fee changes, corporate NPS regulation, exit/withdrawal changes.
Medium: awareness campaigns, portal launches, minor updates.
Low: admin notices, felicitation programs, speeches, events.

Respond ONLY with JSON. No markdown, no preamble.
""".strip()


def _parse_listing(raw_text: str) -> list[dict]:
    """
    Parse the press releases listing page into individual entries using
    the verified markdown structure: [## Title\\n**Issue Date:** DD-MM-YYYY](url)
    """
    entries = []
    for m in ENTRY_PATTERN.finditer(raw_text):
        title = re.sub(r"\s+", " ", m.group("title")).strip()
        day, month, year = m.group("day"), m.group("month"), m.group("year")
        try:
            date_str = f"{year}-{month}-{day}"
            datetime.strptime(date_str, "%Y-%m-%d")  # validate
        except ValueError:
            continue

        url = m.group("url").split("?")[0]  # strip Liferay tracking params

        entries.append({"title": title, "date": date_str, "url": url})

    # Dedup by URL
    seen = set()
    unique = []
    for e in entries:
        if e["url"] in seen:
            continue
        seen.add(e["url"])
        unique.append(e)

    return unique


async def _fetch_listing_entries() -> list[dict]:
    """Fetch and parse the PFRDA press releases listing page."""
    try:
        result = await search_client.extract(urls=[PFRDA_PRESS_RELEASES_URL])
    except Exception as e:
        print(f"[regulatory] Failed to fetch press releases page: {e}")
        return []

    if not result or not result.get("results"):
        print(f"[regulatory] No content returned for press releases page. Raw extract() response: {result!r}")
        return []

    raw_text = result["results"][0].get("raw_content", "")
    entries = _parse_listing(raw_text)
    print(f"[regulatory] Parsed {len(entries)} entries from press releases listing")
    return entries


async def _summarise_entry(entry: dict) -> dict:
    """Fetch the individual release page and summarise it for PensionBox."""
    title = entry["title"]
    url = entry["url"]

    content = ""
    try:
        full = await search_client.extract(urls=[url])
        if full and full.get("results"):
            content = full["results"][0].get("raw_content", "")[:3000]
    except Exception as e:
        print(f"[regulatory] Could not fetch full content for {title[:50]}: {e}")

    prompt = SUMMARY_PROMPT.format(pensionbox_context=PENSIONBOX_CONTEXT) + f"""

Title: {title}
Issue Date: {entry['date']}
URL: {url}
Content:
{content if content else "(No additional content found — summarise from the title alone.)"}
"""

    try:
        response = await llm.ainvoke(prompt)
        raw = response.content.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
    except Exception as e:
        print(f"[regulatory] Failed to summarise: {title[:60]} — {e}")
        data = {"summary": "", "implication": "", "importance": "low"}

    return {
        "title": title,
        "date": entry["date"],
        "url": url,
        "summary": data.get("summary", ""),
        "implication": data.get("implication", ""),
        "importance": data.get("importance", "low"),
    }


async def regulatory_node(state: dict) -> dict:
    """
    Monitors the PFRDA press releases page directly. Lists every release
    found there, unconditionally — no relevance filtering, no staleness
    filtering, no document-type classification. If it's on that page, it's
    a real PFRDA press release and it gets shown. The frontend handles all
    date sorting/filtering (Week / Month / All Time chips).
    """
    print("[regulatory] Fetching PFRDA press releases page...")

    entries = await _fetch_listing_entries()

    if not entries:
        print("[regulatory] No entries parsed — returning empty")
        return {"regulatory_signals": []}

    signals = await asyncio.gather(*[_summarise_entry(e) for e in entries])

    print(f"[regulatory] {len(signals)} press releases listed (unsorted — frontend sorts)")
    return {"regulatory_signals": list(signals)}