from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone
from graph.graph import intelligence_graph
from graph.nodes.regulatory import regulatory_node
from config import COMPETITORS
from graph.graph import intelligence_graph, community_graph

# ── In-memory state ──
latest_signals: list = []
latest_brief: str = None
last_run_at: str = None
latest_regulatory: list = []
last_regulatory_run: str = None
latest_community_signals: list = []
latest_community_brief: str = None
last_community_run_at: str = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[main] Starting Competitor Intelligence Agent...")
    yield


app = FastAPI(
    title="PensionBox Competitor Intelligence Agent",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/run-community")
async def trigger_community_run():
    global latest_community_signals, latest_community_brief, last_community_run_at

    initial_state = {
        "mode": "community",
        "competitors": [],
        "search_plan": {},
        "raw_results": [],
        "community_results": [],
        "signals": [],
        "regulatory_signals": [],
        "brief": None,
        "run_at": None,
        "error": None
    }

    result = await community_graph.ainvoke(initial_state)
    latest_community_signals = result.get("signals", [])
    latest_community_brief = result.get("brief", "")
    last_community_run_at = datetime.now(timezone.utc).isoformat()

    return {
        "message": "Community pipeline complete",
        "total_signals": len(latest_community_signals),
        "last_run_at": last_community_run_at,
        "signals": latest_community_signals
    }

@app.get("/community-signals")
async def get_community_signals():
    return {
        "last_run_at": last_community_run_at,
        "total": len(latest_community_signals),
        "signals": latest_community_signals
    }


@app.get("/community-brief")
async def get_community_brief():
    return {
        "last_run_at": last_community_run_at,
        "total_signals": len(latest_community_signals),
        "brief": latest_community_brief
    }




@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")


@app.post("/run")
async def trigger_run():
    global latest_signals, latest_brief, last_run_at

    initial_state = {
        "competitors": COMPETITORS,
        "search_plan": {},
        "raw_results": [],
        "signals": [],
        "regulatory_signals": [],
        "brief": None,
        "run_at": None,
        "error": None,
        "mode" : "competitor",
        "community_results": []
    }

    result = await intelligence_graph.ainvoke(initial_state)
    latest_signals = result.get("signals", [])
    latest_brief = result.get("brief", "")
    last_run_at = datetime.now(timezone.utc).isoformat()

    return {
        "message": "Pipeline complete",
        "total_signals": len(latest_signals),
        "last_run_at": last_run_at,
        "signals": latest_signals
    }


@app.get("/signals")
async def get_signals():
    return {
        "last_run_at": last_run_at,
        "total": len(latest_signals),
        "signals": latest_signals
    }


@app.get("/brief")
async def get_brief():
    return {
        "last_run_at": last_run_at,
        "total_signals": len(latest_signals),
        "brief": latest_brief
    }


@app.post("/run-regulatory")
async def run_regulatory():
    global latest_regulatory, last_regulatory_run

    result = await regulatory_node({})
    latest_regulatory = result.get("regulatory_signals", [])
    last_regulatory_run = datetime.now(timezone.utc).isoformat()

    return {
        "signals": latest_regulatory,
        "last_run_at": last_regulatory_run,
        "total": len(latest_regulatory)
    }


@app.get("/regulatory-signals")
async def get_regulatory_signals():
    return {
        "signals": latest_regulatory,
        "last_run_at": last_regulatory_run,
        "total": len(latest_regulatory)
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "last_run_at": last_run_at,
        "signals_in_memory": len(latest_signals)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)