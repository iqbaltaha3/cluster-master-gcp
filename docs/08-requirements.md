# 08. Requirements

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | User can upload a dataset (csv, tsv, xlsx, xls, json, parquet). |
| FR-2 | On upload, a Domain Specialist agent researches the dataset's likely domain (Tavily + Groq) and produces a brief shown to the user and shared with every later agent. |
| FR-3 | User can generate a Data Health report (missing values, duplicates, constant columns, high-cardinality columns, correlated features). |
| FR-4 | User can generate an EDA report (summary stats, PCA variance, top correlations, unusual distributions). |
| FR-5 | User can choose a clustering algorithm (KMeans, GMM, Agglomerative, DBSCAN) and parameters, run clustering, and get a narrative quality report. |
| FR-6 | User can generate persona-style Cluster Profiles for each discovered cluster. |
| FR-7 | User can pick two clusters and get a narrative comparison. |
| FR-8 | User can run anomaly detection (Isolation Forest) and get a narrative report on flagged records. |
| FR-9 | User can generate prioritized business recommendations tied to specific clusters. |
| FR-10 | User can generate Executive Dashboard callouts and a full Executive Report synthesizing all prior stages. |
| FR-11 | Every tab has a button to download a PDF containing all reports generated so far, in pipeline order, up to and including that tab. |
| FR-12 | Every agent after the Domain Specialist has access to: the domain brief, one-line takeaways from every prior stage, and its own stage's statistics. |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Secrets (`GROQ_API_KEY`, `TAVILY_API_KEY`) are configured via `.env` only — never entered in the UI, never sent in a request body. |
| NFR-2 | The frontend never renders raw JSON/dicts — only Markdown text returned by the backend. |
| NFR-3 | The LLM never receives raw row-level data — only computed statistics and small samples explicitly built for it. |
| NFR-4 | The system must be runnable locally with two commands (backend + frontend) and via a single `docker compose up`. |
| NFR-5 | A stage's report generation must fail with a clear, actionable error (not a stack trace) if its prerequisites haven't been run yet (e.g. Cluster Profiles before Clustering). |
| NFR-6 | Uploads are capped at a configurable size (`MAX_UPLOAD_MB`, default 50MB) to avoid pathological memory use. |
| NFR-7 | Sessions expire after a configurable inactivity TTL (`SESSION_TTL_SECONDS`, default 6h). |

## Out of scope for v1
- Multi-user auth / accounts.
- Persisting sessions across backend restarts (see ADR 07).
- Editing/regenerating a single paragraph of a report in place.
- Support for datasets that don't fit in memory (no streaming/chunked processing).
