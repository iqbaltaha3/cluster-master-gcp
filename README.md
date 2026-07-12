# ClusterMaster 2.0

AI-powered data segmentation studio — upload a dataset, get a full chain
of specialist-agent reports (Data Health → EDA → Clustering → Cluster
Profiles → Cluster Comparison → Anomaly Detection → Business
Recommendations → Executive Dashboard → Executive Report), each
grounded in a domain-research brief written once at upload time.

## Architecture at a glance

```
frontend/  Streamlit — pure UI client, no business logic, no secrets
backend/   FastAPI — owns state, statistics, LLM (Groq) and search (Tavily) calls
docs/      Architectural decisions + SDLC docs, written chronologically
tests/     Offline unit tests for the pipeline (LLM calls mocked)
```

See `docs/00-index.md` for the full documentation set, including *why*
each major decision was made.

## Quick start

```bash
cp .env.example .env
# fill in GROQ_API_KEY and TAVILY_API_KEY in .env

docker compose up --build
```

- Frontend: http://localhost:8501
- Backend docs (Swagger UI): http://localhost:8000/docs

Or run without Docker — see `docs/10-deployment.md`.

## The pipeline, and how agents share context

1. **Domain Specialist** runs once per upload: sends column names +
   dtypes + a few sample rows to Groq to infer search queries, researches
   them via Tavily, and writes a short domain brief.
2. Every subsequent agent's prompt is built from three things:
   - the domain brief
   - one-line takeaways from every prior stage (`project_memory`),
   - its own stage's freshly computed statistics.
3. Each agent writes its own report and takeaway back to the shared
   `ProjectState`, so context accumulates down the pipeline without any
   agent needing to re-derive what a previous one already established.

No LangGraph — the pipeline is a fixed sequence, not a branching graph;
see `docs/04-adr-shared-state-not-langgraph.md` for the reasoning.

## Repository layout

```
clustermaster/
├── backend/
│   ├── main.py              FastAPI routes
│   ├── config.py            .env-based settings
│   ├── state.py             ProjectState + SessionStore
│   ├── pipeline.py          one function per pipeline stage
│   ├── llm_client.py        the only Groq call site
│   ├── tavily_client.py     the only Tavily call site
│   ├── agents/               prompts + the shared run_agent() helper + domain specialist
│   ├── core/                 clustering/preprocessing/evaluation (reused analysis logic)
│   ├── analytics/             data_health/eda/cluster_profiler/... (reused analysis logic)
│   └── pdf/exporter.py       Markdown -> PDF
├── frontend/
│   ├── app.py                Streamlit pages
│   └── api_client.py         all HTTP calls to the backend
├── docs/                      ADRs + SDLC docs, numbered chronologically
├── tests/                     offline pipeline tests
├── docker/                    Dockerfiles for backend & frontend
├── docker-compose.yml
└── .env.example
```

## Running tests

```bash
pip install -r backend/requirements.txt pytest
pytest tests/ -v
```
