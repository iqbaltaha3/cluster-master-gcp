# ADR 05: API keys live only in backend `.env`, never in the UI

**Status:** Accepted
**Date:** Step 5 of the v2.0 rebuild

## Context
v1 had a sidebar text input for the Anthropic API key, stored in
`st.session_state` and pushed into `os.environ` at request time. This is
a common Streamlit-prototype pattern, but it means the key touches the
browser process, is visible in browser dev tools' network/memory
inspection, and has to be re-entered per session.

## Decision
- `GROQ_API_KEY` and `TAVILY_API_KEY` are read once, at backend startup,
  from a `.env` file via `python-dotenv` (`backend/config.py`).
- No FastAPI route accepts a key as a request parameter. No Streamlit
  widget asks for one.
- `.env` is git-ignored (`.gitignore`); `.env.example` documents the
  required variables with placeholder values.
- If a key is missing, the relevant call fails fast with a clear
  `RuntimeError` (`require_groq_key()` / a graceful degrade path for
  Tavily — see ADR 03) rather than silently proceeding or prompting the
  user for one.

## Consequences
- The frontend process never has access to either secret — verified by
  the fact that `frontend/` has zero references to `GROQ_API_KEY` or
  `TAVILY_API_KEY`.
- Rotating a key means editing one `.env` file and restarting the
  backend — no per-user re-entry.
- Multi-tenant deployments (different keys per customer) are out of
  scope for v1; see `13-roadmap.md`.
