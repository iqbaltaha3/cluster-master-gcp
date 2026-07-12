# ADR 04: Shared state object instead of LangGraph

**Status:** Accepted
**Date:** Step 4 of the v2.0 rebuild

## Context
The pipeline (Data Health → EDA → Clustering → Cluster Profiles → Cluster
Comparison → Anomaly Detection → Recommendations → Executive Dashboard →
Executive Report) is a **fixed, linear DAG**. Order never changes,
there's no conditional branching between agents, and no agent needs to
loop back and re-run an earlier one automatically. Each stage is
triggered by a human clicking a button in the UI, not by an agent
deciding what runs next.

## Decision
Do not use LangGraph (or any graph-orchestration library). Instead:
- `backend/state.py:ProjectState` is a plain dataclass holding
  everything a stage might need: the dataframe, computed stats,
  `domain_brief`, `project_memory` (one-line takeaways per stage), and
  finished `reports` (Markdown per stage).
- `backend/pipeline.py` has one function per stage. Each function reads
  what it needs from `ProjectState`, computes its stage's statistics,
  calls the shared `run_agent()` helper, and writes its results back.
- FastAPI routes in `main.py` are the actual "orchestrator" — a stage's
  route is only callable once its prerequisite state exists (e.g.
  Cluster Profiles requires `state.labels` to be set, checked explicitly
  and returned as a 409 if missing).

## Consequences
- No new orchestration framework to learn, version, or debug — it's a
  dict-like object and a list of functions.
- Prerequisite checks are explicit `if state.x is None: raise
  StageError(...)` calls, not graph edge conditions — more verbose per
  function, but each function is independently readable without needing
  to trace a graph definition elsewhere.
- If a future requirement introduces real branching (e.g. "if data health
  is bad, auto-suggest remediation and re-run"), that's the point to
  revisit this decision — LangGraph (or a simple state machine) would
  earn its complexity then, not before.
