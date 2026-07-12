# ADR 01: Split into a FastAPI backend and a thin Streamlit frontend

**Status:** Accepted
**Date:** Step 1 of the v2.0 rebuild

## Context
v1 was a single Streamlit app: file upload, statistics, and LLM calls all
lived in `app/main.py`, with `st.session_state` as the only state
mechanism. This meant:
- Raw dicts occasionally got rendered straight to the screen (the "JSON on
  screen" problem).
- API keys were typed into a sidebar text input, stored in
  `session_state`, and pushed into `os.environ` at runtime.
- There was no way to reuse the analysis logic outside of a Streamlit
  process (no API, no CLI, no batch mode).
- Streamlit reruns the whole script top-to-bottom on every interaction,
  which made it tempting to conflate "business logic" with "widget
  layout."

## Decision
Split the system into two processes:
- **`backend/`** — a FastAPI service that owns all state, all statistics
  computation, and all LLM/Tavily calls. It exposes a small REST API and
  returns only two kinds of payloads: small metadata objects (row counts,
  column names) and finished Markdown strings. It never returns a raw
  stats dict to the client.
- **`frontend/`** — a Streamlit app that is a pure client of that API. It
  builds requests, shows spinners, and calls `st.markdown()` on whatever
  text comes back. It has no analytics code and no LLM client code.

## Consequences
- Fixes the "JSON on screen" problem structurally: the frontend has
  nothing to render except Markdown, because that's all the API returns.
- Secrets (Groq, Tavily) never need to reach the frontend process at all.
- The backend can be used from anywhere — a CLI, a notebook, a different
  frontend, automated tests — since it's a normal REST API.
- Cost: two processes to run instead of one; see
  `10-deployment.md` for how that's made simple with Docker Compose.
