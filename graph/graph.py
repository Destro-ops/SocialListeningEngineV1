from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes.supervisor import supervisor_node
from graph.nodes.researcher import researcher_node
from graph.nodes.analyst import analyst_node
from graph.nodes.dedup import dedup_node
from graph.nodes.briefing import briefing_node


def should_continue_after_research(state: AgentState) -> str:
    """
    Edge condition after researcher.
    If no results found, skip straight to briefing.
    """
    if not state.get("raw_results"):
        print("[graph] No results found — skipping to briefing")
        return "briefing"
    return "analyst"


def should_continue_after_analyst(state: AgentState) -> str:
    """
    Edge condition after analyst.
    If no relevant signals, skip dedup straight to briefing.
    """
    if not state.get("signals"):
        print("[graph] No signals found — skipping to briefing")
        return "briefing"
    return "dedup"


def build_graph() -> StateGraph:
    """Build and compile the competitor intelligence graph."""

    graph = StateGraph(AgentState)

    # --- Add nodes ---
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("dedup", dedup_node)
    graph.add_node("briefing", briefing_node)

    # --- Entry point ---
    graph.set_entry_point("supervisor")

    # --- Edges ---
    # Supervisor always goes to researcher
    graph.add_edge("supervisor", "researcher")

    # Researcher → analyst OR briefing (if no results)
    graph.add_conditional_edges(
        "researcher",
        should_continue_after_research,
        {
            "analyst": "analyst",
            "briefing": "briefing"
        }
    )

    # Analyst → dedup OR briefing (if no signals)
    graph.add_conditional_edges(
        "analyst",
        should_continue_after_analyst,
        {
            "dedup": "dedup",
            "briefing": "briefing"
        }
    )

    # Dedup always goes to briefing
    graph.add_edge("dedup", "briefing")

    # Briefing → END
    graph.add_edge("briefing", END)

    return graph.compile()


# Compile once at module level — reused across runs
intelligence_graph = build_graph()