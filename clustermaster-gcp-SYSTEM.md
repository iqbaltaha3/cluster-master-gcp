# SYSTEM.md — ClusterMaster

Technical/architectural reference. For a plain-English tour of *what this does*, see the README. This document is for anyone who needs to modify, extend, deploy, or debug the codebase.

---

## 1. Repository layout

```
clustermaster/
├── backend/
│   ├── main.py                 FastAPI routes — the only orchestrator in the system
│   ├── config.py               .env-based Settings singleton
│   ├── state.py                ProjectState (dataclass) + SessionStore (in-memory)
│   ├── pipeline.py              one run_* function per pipeline stage
│   ├── llm_client.py            the ONLY call site for Groq (call_groq())
│   ├── tavily_client.py          the ONLY call site for Tavily (tavily_search())
│   ├── schemas.py                 Pydantic request/response models
│   ├── utils.py                    to_jsonable(), safe_download_filename()
│   ├── agents/
│   │   ├── base.py                  run_agent() — shared prompt assembly + call_groq + memory write
│   │   ├── domain_specialist.py       runs once per upload; produces domain_brief
│   │   └── prompts.py                  STAGE_PROMPTS dict, STAGE_LABELS dict, DOMAIN_SPECIALIST_SYSTEM
│   ├── core/                          reused analysis logic (not agent-specific)
│   │   ├── data_loader.py               reads uploaded file -> DataFrame
│   │   ├── preprocessing.py              clean_dataset(), build_feature_matrix(), get_column_types()
│   │   ├── clustering.py                  KMeans / GMM / Agglomerative / DBSCAN wrapper
│   │   ├── evaluation.py                   clustering quality metrics
│   │   ├── reduction.py                     PCA to 2D for the scatter chart
│   │   └── visualization.py                  (plotting helpers; not currently wired into PDF — see §7)
│   ├── analytics/                       stage-specific statistics computation
│   │   ├── data_health.py, eda.py, cluster_profiler.py,
│   │   │   cluster_comparison.py, anomaly_detection.py, recommendation_engine.py
│   └── pdf/exporter.py                 build_pdf(state, upto) — Markdown -> HTML -> PDF
├── frontend/
│   ├── app.py                          Streamlit UI — zero business logic
│   └── api_client.py                    every HTTP call to the backend lives here, nowhere else
├── docs/                                13 ADRs + SDLC docs, numbered chronologically (see docs/00-index.md)
├── tests/test_pipeline.py                offline pipeline tests, call_groq mocked
├── docker/{backend,frontend}.Dockerfile
├── docker-compose.yml
└── cloudbuild.yaml                        Cloud Run CI/CD (Google Cloud Build)
```

**Reading order for a new contributor:** `state.py` → `pipeline.py` → `main.py` → `agents/base.py`. That's the entire request lifecycle; everything in `core/` and `analytics/` is just "what statistics does this stage need," swappable independently of the pipeline shape.

---

## 2. Request lifecycle (how one report actually gets built)

```
POST /session                     → SessionStore.create() → new ProjectState, empty
POST /session/{id}/upload          → data_loader.load_dataset()
                                       → run_domain_brief()  [Groq + Tavily, once]
POST /session/{id}/report/{stage}  → pipeline.run_<stage>(state, ...)
                                       1. compute stats via core/ or analytics/
                                       2. stash anything downstream stages need on `state`
                                       3. run_agent(state, stage_key, stats)
                                            → build prompt: domain_brief + project_memory + stats
                                            → call_groq()
                                            → state.reports[stage_key] = report_md
                                            → state.project_memory[stage_key] = first-line takeaway
                                       4. return ReportResponse(markdown, stats)
GET /session/{id}/pdf?upto=stage    → build_pdf() slices STAGE_ORDER up to `upto`
GET /session/{id}/export/clustered_data → cleaned_df + labels column → CSV StreamingResponse
```

There is **no** graph/orchestration library. `main.py`'s routes *are* the orchestrator: each route is only reachable in a valid order because `pipeline.py` raises `StageError` (→ HTTP 409) if a prerequisite hasn't run yet (e.g. Cluster Profiles requires `state.labels is not None`).

---

## 3. State model

`backend/state.py`:

- **`ProjectState`** — one plain dataclass per active session: raw `df`, `cleaned_df`, `X` (feature matrix), `labels`, `domain_brief`, `stats` (dict keyed by stage), `reports` (Markdown per stage), `project_memory` (one-line takeaway per stage).
- **`SessionStore`** — a plain Python `dict` mapping `session_id -> ProjectState`, with TTL-based eviction (`SESSION_TTL_SECONDS`, default 6h).
- **`STAGE_ORDER`** — the canonical list defining both prerequisite checks and PDF slicing order.

This is intentionally **not** persisted anywhere durable. See §6 for the consequences and upgrade path.

---

## 4. Key architectural decisions (condensed from `docs/`)

| # | Decision | Why |
|---|---|---|
| ADR01 | FastAPI backend + thin Streamlit frontend, split into two processes | v1 was one Streamlit script; business logic, secrets, and UI were tangled together, and raw dicts sometimes got rendered straight to screen. The backend now returns **only** small metadata objects and finished Markdown — never a raw stats dict — so the frontend structurally cannot leak internals. |
| ADR02 | All LLM calls go through Groq, and through exactly one function (`call_groq()`) | v1 called Anthropic directly from multiple places. Now every agent, everywhere, calls one function — swapping providers or adding per-agent model routing later is a one-file change. |
| ADR03 | A "Domain Specialist" agent runs once per upload, before the 9-stage pipeline | Individual stage agents only see their own narrow statistics and have no idea what kind of dataset they're looking at. One upfront agent infers the domain, runs a few web searches, and writes a short brief that's prepended to every later prompt — paying the domain-research cost once, not 9 times. |
| ADR04 | Shared mutable state object instead of LangGraph (or any DAG/graph framework) | The pipeline is a **fixed, linear** sequence — no branching, no agent decides what runs next. A plain dataclass + a list of functions is simpler to read and debug than a graph definition, at the cost of writing prerequisite checks by hand in each function. |
| ADR05 | Secrets live only in backend `.env`, never touch the frontend or a request body | v1 had a sidebar text input for the API key, visible in browser devtools. Now `frontend/` has zero references to either secret env var — verified structurally, not just by convention. |
| ADR06 | PDF export is cumulative and stage-scoped ("download till here") | Rendering uses pure-Python `markdown2` + `xhtml2pdf` (no headless-browser dependency in the image). `build_pdf(state, upto)` is a pure function of state + a stage name, so it's testable without a browser or LLM call. |
| ADR07 | Sessions are in-memory, single-process, with a documented Redis upgrade path | Accepted for v1 given a single-instance deployment target; the seam (`store.create()` / `store.get()`) is already isolated so swapping in Redis later doesn't touch route or agent code. |

---

## 5. Data privacy design (a real architectural constraint, not just a policy)

- The Domain Specialist (`agents/domain_specialist.py`) sends Groq **only**: column names, dtypes, row count, and a handful of per-column example values sampled *independently per column* (`_column_examples()`) — never full linked rows — unless `SEND_SAMPLE_ROWS_TO_LLM=true` is explicitly set.
- Every other stage sends only aggregate statistics (counts, means, cluster sizes, evaluation metrics) to Groq — never raw rows. This is enforced structurally by what `pipeline.py`'s `run_*` functions build into the `stats` dict, not by a separate filter layer — worth knowing if adding a new stage: don't put a raw DataFrame slice into the `stats` dict passed to `run_agent()`.
- `_json_safe()` in `agents/base.py` also truncates any oversized stats payload to `LLM_MAX_CONTEXT_CHARS` (default 8000) before it reaches Groq.

---

## 6. Known shortcomings (from `docs/13-roadmap.md`, verified against code)

- **No auth.** Anyone who can reach the backend can create sessions and spend Groq/Tavily quota. There's a shared-secret `X-API-Key` header gate (`require_api_key` in `main.py`) but it's a single static secret, not per-user auth — fine for an internal/local tool, not for open public deployment.
- **In-memory, single-process sessions** (ADR07). A backend restart drops every in-progress session. Cannot run multiple `uvicorn` workers behind a load balancer — each would have its own independent session dict.
- **Naive takeaway extraction.** `_extract_takeaway()` just grabs the first non-empty line of a report and truncates to 220 chars. It works because prompts are steered to lead with a clear headline, but it's a heuristic, not a real summarization step — a badly-formatted report could produce a poor takeaway that then quietly degrades every downstream agent's context.
- **No automatic downstream invalidation.** Re-running Clustering with different parameters does **not** invalidate or auto-regenerate Cluster Profiles, Cluster Comparison, Anomaly Detection, Recommendations, or the two executive stages — a user can end up looking at reports that describe an earlier clustering run.
- **No streaming.** Report generation is one blocking `call_groq()` per stage; the UI shows a spinner rather than streaming tokens.
- **Minimal PDF styling.** One shared CSS block, no charts embedded (despite `core/visualization.py` existing, it isn't currently wired into `pdf/exporter.py`), no branding slot.
- **DBSCAN's `n_clusters` isn't meaningful** — the clustering route's guard (`n_clusters_requested > n_rows`) only applies to KMeans/GMM/Agglomerative; DBSCAN takes `eps`/`min_samples` instead, and can return `-1` (noise) labels that downstream stages need to handle as "not a real cluster."

---

## 7. Things to know before extending it

- **Adding a new pipeline stage**: add a `run_<stage>()` function in `pipeline.py`, a prompt in `agents/prompts.py::STAGE_PROMPTS`, a label in `STAGE_LABELS`, a route in `main.py`, and an entry in `state.py::STAGE_ORDER` (position matters — it drives both prerequisite checks and PDF slicing).
- **`core/` vs `analytics/`**: `core/` holds general-purpose data-science building blocks (preprocessing, clustering, PCA, evaluation) that don't know about "stages" or agents. `analytics/` holds stage-specific statistics computation (data health, EDA, cluster profiling, comparison, anomalies, recommendations) that plug straight into `pipeline.py`. New reusable math goes in `core/`; new stage-specific number-crunching goes in `analytics/`.
- **`to_jsonable()` in `utils.py`** exists because raw clustering output (numpy types, numpy arrays) isn't directly JSON-serializable — any new stat added to a stage's `stats` dict that includes numpy scalars/arrays needs to pass through this before being returned over the API.
- **Tavily is optional at the code level** — if `TAVILY_API_KEY` is unset, `tavily_search()` degrades to a `"(search failed for '...')"` string per query rather than raising, so the Domain Specialist still produces a brief (a less-informed one) instead of blocking the upload entirely.
