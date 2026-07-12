# 12. Runbook

Quick reference for common problems and what to do about them.

## "Could not reach the backend" in the Streamlit app
- Backend isn't running, or `BACKEND_URL` in the frontend environment
  doesn't match where it's actually listening.
- Check: `curl http://localhost:8000/health` should return `{"status":"ok"}`.
- In Docker Compose, the frontend must use `http://backend:8000`, not
  `http://localhost:8000` (see `docker-compose.yml`).

## Upload succeeds but domain brief looks generic / says "not configured"
- `TAVILY_API_KEY` is missing or invalid in `.env`. The system degrades
  gracefully (ADR 03) rather than failing the upload — check backend logs
  for `(search failed for ...)` or `(Tavily not configured ...)` inside
  the brief text.

## A report generation call returns 503
- `GROQ_API_KEY` is missing or invalid. Fix `.env` and restart the
  backend (`docker compose restart backend` or re-run `uvicorn`).

## A report generation call returns 409
- The stage's prerequisite hasn't been run yet (e.g. requesting Cluster
  Profiles before running Clustering). The `detail` field names exactly
  what to run first. This is expected behavior, not a bug.

## "Unknown or expired session_id" (404)
- The backend restarted (sessions are in-memory, ADR 07) or the session
  TTL (`SESSION_TTL_SECONDS`) elapsed. Re-upload the dataset to get a
  fresh session; the frontend does this automatically on next upload.

## PDF download button is disabled
- No report has been generated for that tab yet. Click the "Generate ..."
  button first — the download button enables once `state.reports[stage]`
  exists.

## Upload rejected with 413
- File exceeds `MAX_UPLOAD_MB` (default 50MB). Either raise the limit in
  `.env` (mind backend memory) or reduce the dataset size.

## High latency on Domain Specialist / Executive Report stages
- These make multiple sequential calls (Groq for query generation +
  Tavily searches + Groq synthesis, or a large PRIOR FINDINGS context for
  the Executive Report). This is expected; the frontend shows a spinner.
  If it's consistently too slow, consider a faster `GROQ_MODEL`.

## Where to look first when something's wrong
1. Backend terminal / `docker compose logs backend` — actual exceptions
   surface here (FastAPI logs the full traceback for 500s).
2. `GET /docs` (Swagger UI) — manually replay the failing request outside
   the Streamlit UI to isolate frontend vs. backend issues.
