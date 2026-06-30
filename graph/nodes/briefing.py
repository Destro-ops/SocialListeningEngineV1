from datetime import datetime, timezone
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from config import BRIEFING_MODEL, PENSIONBOX_CONTEXT

llm = ChatOpenAI(model=BRIEFING_MODEL, temperature=0.1)  

BRIEFING_PROMPT = """
You are a senior intelligence analyst writing a daily competitive brief for 
the founding team of PensionBox.in.

{pensionbox_context}

Based on the signals below, write a sharp, concise intelligence brief.
Be direct. No fluff. Write like you're briefing a busy founder.

Format EXACTLY like this:

---
## PensionBox Competitive Intelligence Brief
**{date}**

### Executive Summary
2-3 sentences. What's the most important thing that happened today 
across all competitors? What's the headline?

### Competitor Activity

For each competitor that has signals, write:

#### [Competitor Name]
- **[Signal Type]** [IMPORTANCE BADGE: 🔴 HIGH / 🟡 MEDIUM / ⚪ LOW]
  What happened: [1-2 sentences]
  What it means for PensionBox: [specific implication]
  Source: [URL]

### Recommended Actions
Numbered list of 2-4 concrete actions PensionBox should consider 
based on today's intelligence. Be specific, not generic.

### No Activity
List competitors with no significant signals today.
---

Signals:
{signals}

If there are no signals at all, write a brief stating no significant 
competitor activity was detected today.
""".strip()


def _format_signals(signals: list) -> str:
    """Format signals into readable block for the prompt."""
    if not signals:
        return "No signals found."

    lines = []
    for i, s in enumerate(signals):
        lines.append(f"""
Signal {i+1}:
Competitor: {s.get('competitor')}
Title: {s.get('title')}
Importance: {s.get('importance')}
Signal Type: {s.get('signal_type')}
Summary: {s.get('summary')}
Implication: {s.get('implication')}
URL: {s.get('url')}
Also covered by: {', '.join(s.get('also_covered_by', []))}
""".strip())

    return "\n\n".join(lines)


async def briefing_node(state: AgentState) -> dict:
    """
    Synthesises all signals into a daily intelligence brief.
    """
    signals = state.get("signals", [])
    date = datetime.now(timezone.utc).strftime("%d %B %Y")

    print(f"[briefing] Writing brief for {len(signals)} signals...")

    prompt = BRIEFING_PROMPT.format(
        pensionbox_context=PENSIONBOX_CONTEXT,
        date=date,
        signals=_format_signals(signals)
    )

    try:
        response = await llm.ainvoke(prompt)
        brief = response.content.strip()

        print("[briefing] Brief written successfully.")
        return {
            "brief": brief,
            "run_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        print(f"[briefing] ERROR: {e}")
        return {
            "brief": "Brief generation failed.",
            "error": str(e),
            "run_at": datetime.now(timezone.utc).isoformat()
        }