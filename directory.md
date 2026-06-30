competitor_intel/
├── main.py
├── config.py
├── .env
├── requirements.txt
│
├── graph/
│   ├── __init__.py
│   ├── state.py          ← LangGraph state schema
│   ├── graph.py          ← builds the graph
│   └── nodes/
│       ├── __init__.py
│       ├── supervisor.py
│       ├── researcher.py
│       ├── analyst.py
│       ├── dedup.py
│       └── briefing.py
│
├── tools/
│   ├── __init__.py
│   ├── web_search.py     ← Tavily tool
│   └── rss_fetch.py      ← reuse fetcher logic
│
├── dashboard.py
└── scheduler.py