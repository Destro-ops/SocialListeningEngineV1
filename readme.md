# PensionBox Social Listening & Competitor Intelligence Platform

An AI-powered competitive intelligence platform built for PensionBox.in. Uses a multi-agent LangGraph pipeline to monitor competitors, track PFRDA regulatory releases, and surface actionable intelligence for the PensionBox team.

---

## What It Does

- **Competitor Intelligence** — monitors HDFC Pension, ICICI Prudential, Axis Bank NPS, DSP Pension Fund, and Aditya Birla Sun Life Pension across the web for product launches, partnerships, hiring signals, pricing changes, and marketing pushes
- **Regulatory Monitor** — tracks PFRDA press releases and circulars, fetches full PDF content, and generates PensionBox-specific implications
- **Community Monitor** - tracks posts on social media (reddit, twitter, quora)regarding nps, epf and etc. Categorizes them based on sentiment.
- **AI Briefing** — every run produces a structured intelligence brief written by the agent, not just raw articles
- **Glassmorphism Dashboard** — served via FastAPI, no separate frontend server needed

---

## Architecture

```
Supervisor Agent
    → generates targeted search queries per competitor

Researcher Agent
    → fires all queries concurrently via Tavily

Analyst Agent
    → classifies each result: signal type, importance, implication for PensionBox

Dedup Agent
    → clusters same-story articles into single signals

Briefing Agent
    → writes a daily intelligence brief

Regulatory Node
    → separate pipeline for PFRDA press releases
    → fetches PDF content via Tavily Extract
    → generates implication per release
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph |
| LLM | OpenAI GPT (gpt-5.4-mini) |
| Web Search | Tavily API |
| Backend | FastAPI + Uvicorn |
| Frontend | Vanilla HTML/CSS/JS (glassmorphism) |
| Language | Python 3.11+ |

---

## Prerequisites

- Python 3.11 or higher
- pip
- A terminal (PowerShell on Windows, bash on Mac/Linux)

---

## API Keys Required

### 1. OpenAI API Key
**Where to get it:** https://platform.openai.com

**Steps:**
1. Create an account at platform.openai.com
2. Go to **API Keys** → **Create new secret key**
3. Copy the key (starts with `sk-`)

**Plan needed:**
- Minimum: **Pay-as-you-go** (add $5 minimum credit)
- Recommended spend: $5-10/month for running 2-3 times a week 
- Free tier has no API access — you must add billing
- Model used: `gpt-5.4-mini`
- Estimated cost per pipeline run: $0.5 for competitor and $0.1 for community depending on result volume
- Rate limits increase automatically as you spend more

**Rate limit tiers:** https://platform.openai.com/account/rate-limits

---

### 2. Tavily API Key
**Where to get it:** https://tavily.com

**Steps:**
1. Sign up at app.tavily.com
2. Go to **API Keys** → copy your key (starts with `tvly-`)

**Plan needed:**
- **Free tier:** 1,000 API credits/month
  - Enough for ~5-10 pipeline runs/month
  - Good for testing and light use
- **Researcher plan ($30/month):** 10,000 credits/month
  - Recommended for daily use
  - Each pipeline run uses ~100-200 credits (20 Tavily searches × 5-10 results each)
  - Each regulatory run uses ~20-30 credits
  - Each community run uses around 35 credits
- **Advanced search depth** is used by default — costs 2 credits per search vs 1 for basic
- To reduce credit usage: change `search_depth="advanced"` to `search_depth="basic"` in `researcher.py` and `regulatory.py`


```


## Setup Instructions

### Step 1 — Clone or download the project

```bash
cd your-projects-folder
cd competitor_intel
```

### Step 2 — Create a virtual environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt.

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create your `.env` file

Create a file called `.env` in the project root:

```
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvly-your-key-here
```

**Never commit this file to git.** Add `.env` to your `.gitignore`.

### Step 5 — Verify config

Open `config.py` and confirm:

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

SUPERVISOR_MODEL = "gpt-5.4-mini"
ANALYST_MODEL = "gpt-5.4-mini"
RESEARCH_MODEL = "gpt-5.4-mini"
BRIEFING_MODEL = "gpt-5.4-mini"

COMPETITORS = [
    "HDFC Pension",
    "ICICI Prudential Pension",
    "Axis Bank NPS",
    "DSP Pension Fund",
    "Aditya Birla Sun Life Pension",
]

MAX_ARTICLES_FOR_LLM = 20   # keep low if on free/low tier API plans
```

### Step 6 — Run the server

```bash
python main.py
```

You should see:
```
[main] Starting Competitor Intelligence Agent...
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 7 — Open the dashboard

Open your browser and go to:
```
http://localhost:8001
```

---

## Using the Dashboard

### Live Feed
- Click **⚡ Run Intelligence Feed** to run the full competitor pipeline
- Results are sorted by importance (High → Medium → Low)
- Use tabs to filter by signal type: Product Launch, Partnership, Hiring, Pricing, Regulatory, Marketing, Market News
- Use sidebar filters to filter by importance or specific competitor

### Previous Results
- Every competitr run only is automatically saved to `runs.json`
- Last 5 runs are stored
- Click any run timestamp to expand and browse that run's signals

### Regulatory Monitor
- Click **⚡ Fetch Releases** to run the PFRDA pipeline separately

- Each card shows: summary, key quote from the document, and PensionBox implication

### Community Monitor
- Click  **Run community feed** to get posts from social media


---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the frontend dashboard |
| `POST` | `/run` | Runs the full competitor intelligence pipeline |
| `GET` | `/signals` | Returns latest signals from last run |
| `GET` | `/brief` | Returns the latest AI-written brief |
| `POST` | `/run-regulatory` | Runs the PFRDA regulatory pipeline |
| `GET` | `/regulatory-signals` | Returns latest regulatory signals |
| `GET` | `/health` | Health check + last run timestamp |

---

## Tuning for Your API Plan

### If you're on OpenAI low tier:

In `config.py`:
```python
MAX_ARTICLES_FOR_LLM = 15
```

In `analyst.py` — reduce semaphore:
```python
semaphore = asyncio.Semaphore(2)
```

Add billing at platform.openai.com/billing to increase rate limits automatically.

### If you're on OpenAI Tier 2+:

In `config.py`:
```python
MAX_ARTICLES_FOR_LLM = 60
```

In `analyst.py`:
```python
semaphore = asyncio.Semaphore(20)
```

Runs complete in 2-3 minutes.

### If you're on Tavily free tier (1,000 credits/month):

In `researcher.py` and `regulatory.py`:
```python
search_depth="basic"   # uses 1 credit instead of 2
max_results=3          # reduces from 5
```

In `config.py`:
```python
MAX_ARTICLES_FOR_LLM = 15
```

---

## Adding or Removing Competitors

In `config.py`:
```python
COMPETITORS = [
    "HDFC Pension",
    "ICICI Prudential Pension",
    "Axis Bank NPS",
    "DSP Pension Fund",
    "Aditya Birla Sun Life Pension" # add new competitor here
    
]
```

No other changes needed. The supervisor agent automatically generates search queries for any competitor in this list.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `insufficient_quota` | OpenAI account out of credits | Add billing at platform.openai.com/billing |
| `rate_limit_error 429` | Too many concurrent API calls | Reduce `MAX_ARTICLES_FOR_LLM` and semaphore in `analyst.py` |
| `[researcher] FAILED` | Tavily API key invalid or out of credits | Check key at app.tavily.com |
| `500 Internal Server Error` | Check terminal for full traceback | Usually an API key or rate limit issue |
| Dashboard shows no signals | Backend not running | Make sure `python main.py` is running |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `TAVILY_API_KEY` | Yes | Tavily search API key |

---

## Notes

- `runs.json` is created automatically on first run — stores last 5 pipeline results
- The pipeline does not run on server startup — only when you click the button
- All data is stored in memory — restarting the server clears current session signals (previous runs in `runs.json` persist)
- PFRDA regulatory results are not persisted between restarts by design