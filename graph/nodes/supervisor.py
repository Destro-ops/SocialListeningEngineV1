import json
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from config import SUPERVISOR_MODEL, PENSIONBOX_CONTEXT, COMPETITORS

from langchain_anthropic import ChatAnthropic
llm = ChatOpenAI(model=SUPERVISOR_MODEL, temperature=0)

from datetime import datetime, timezone

def get_supervisor_prompt() -> str:
    now = datetime.now(timezone.utc)
    today = now.strftime("%d %B %Y")
    month = now.strftime("%B")
    year = now.strftime("%Y")

    return f"""
You are a strategic intelligence coordinator for PensionBox.in.

{{pensionbox_context}}

Today's date is {today}. You are generating search queries to find what competitors 
are doing RIGHT NOW in {month} {year}.

Your job: Given a list of competitors, generate smart, targeted search queries
to find what each competitor is doing that could affect PensionBox.

For each competitor generate valid search queries covering:
- there is no fixed number of queries per competitor generate as many as needed to cover all relevant angles
1. New product or feature launches
2. Partnerships with HR tech platforms (Darwinbox, Keka, greytHR, Razorpay)
3. Regulatory responses (new PFRDA/SEBI compliance features)
4. Hiring signals (are they scaling their NPS/benefits team?)
5. Pricing changes or promotional campaigns

CRITICAL: Every query must be within this timeframe "{month} {year}".
The goal is to find news and announcements in {month} {year} only.
Never generate generic timeless queries — always anchor to the current month.

Respond ONLY with a JSON object like this:
{{{{
  "HDFC Pension": [
    "HDFC Pension NPS corporate product launch",
    "HDFC Pension Darwinbox integration ",
    "HDFC Pension relationship manager hiring "
  ]
}}}}

Be specific. Generic queries waste search budget.
Competitors: {{competitors}}
""".strip()


async def supervisor_node(state: AgentState) -> dict:
    """
    Decides what to search for each competitor.
    Returns search queries per competitor.
    """
    print("[supervisor] Generating search strategy...")

    prompt = get_supervisor_prompt().format(
    pensionbox_context=PENSIONBOX_CONTEXT,
    competitors=", ".join(state["competitors"]),
)

    response = await llm.ainvoke(prompt)
    raw = response.content.strip()

    # Clean markdown if LLM wraps in backticks
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        search_plan = json.loads(raw)
        print(f"[supervisor] Generated queries for {len(search_plan)} competitors")

        return {
            "search_plan": search_plan,
            "raw_results": []  # initialize empty, researcher fills this
        }

    except json.JSONDecodeError:
        print("[supervisor] Failed to parse search plan")
        return {
            "search_plan": {},
            "raw_results": [],
            "error": "Supervisor failed to generate search plan"
        }