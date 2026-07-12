# ClusterMaster Documentation

This folder is written **chronologically** — in the order decisions were
actually made while building v2.0 (FastAPI + Streamlit + multi-agent
pipeline). Read top to bottom for the story of the system, or jump
straight to the doc you need.

## Architectural Decision Records (ADRs)
1. [01-adr-fastapi-streamlit-split.md](01-adr-fastapi-streamlit-split.md) — why the frontend/backend split
2. [02-adr-groq-over-anthropic.md](02-adr-groq-over-anthropic.md) — why Groq for LLM calls
3. [03-adr-domain-specialist-agent.md](03-adr-domain-specialist-agent.md) — why a domain-research agent runs first
4. [04-adr-shared-state-not-langgraph.md](04-adr-shared-state-not-langgraph.md) — why a shared state object instead of LangGraph
5. [05-adr-secrets-in-env-not-ui.md](05-adr-secrets-in-env-not-ui.md) — why API keys live only in `.env`
6. [06-adr-pdf-export-per-stage.md](06-adr-pdf-export-per-stage.md) — why PDF export is cumulative and stage-scoped
7. [07-state-persistence-tradeoff.md](07-state-persistence-tradeoff.md) — why sessions are in-memory (and the upgrade path)

## SDLC documents
8. [08-requirements.md](08-requirements.md) — functional & non-functional requirements
9. [09-api-contract.md](09-api-contract.md) — REST API reference
10. [10-deployment.md](10-deployment.md) — how to run locally, in Docker, and in production
11. [11-testing-strategy.md](11-testing-strategy.md) — what's tested and how
12. [12-runbook.md](12-runbook.md) — operational runbook (incidents, common errors)
13. [13-roadmap.md](13-roadmap.md) — known limitations and what's next
