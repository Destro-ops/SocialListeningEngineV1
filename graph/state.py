# graph/state.py
from typing import TypedDict, List, Optional

class Signal(TypedDict):
    competitor: str
    title: str
    url: str
    summary: str
    source: str
    signal_type: str        # product_launch, hiring, partnership etc
    importance: str         # high, medium, low
    implication: str        # what this means for PensionBox
    published_at: str

class AgentState(TypedDict):
    # Input
    competitors: List[str]          # ["HDFC Pension", "ICICI", ...]
    search_plan: dict                   # {"HDFC Pension": ["news", "blogs"], ...}
    # Research phase
    raw_results: List[dict] 
       
    regulatory_signals: List[dict] 
    # Analysis phase
    signals: List[Signal]           # filtered, classified signals

    # Output
    brief: Optional[str]            # final markdown brief with citations
    run_at: Optional[str]           # timestamp
    error: Optional[str]            # if something goes wrong