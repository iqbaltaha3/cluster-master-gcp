# 13. Roadmap / Known Limitations

Written last, after the system was built end-to-end, as an honest list of
what v1 doesn't do yet.

## Known limitations
- **Single-process, in-memory sessions** — see ADR 07. No horizontal
  scaling, no restart durability.
- **No auth** — anyone who can reach the backend can create sessions and
  spend Groq/Tavily quota. Fine for an internal tool or local use; not
  fine for an open public deployment as-is.
- **One-line takeaway extraction is naive** — `_extract_takeaway()` in
  `backend/agents/base.py` just takes the first non-empty line of a
  report. It works well because prompts are steered to lead with a clear
  headline, but it's a heuristic, not a summarization model call.
- **PDF styling is minimal** — one shared CSS block, no company branding
  slot, no charts embedded (text-only reports).
- **No streaming responses** — report generation is a single blocking
  Groq call; the UI shows a spinner rather than streaming tokens in.
- **No automatic re-run on upstream change** — if a user re-runs
  Clustering with different parameters, downstream reports (Cluster
  Profiles, Recommendations, etc.) are NOT automatically invalidated or
  regenerated; the user must manually re-generate them.

## Likely next steps, roughly in priority order
1. **Auth + per-user rate limiting** before any public deployment.
2. **Redis-backed `SessionStore`** to unlock multi-worker scaling and
   restart durability (see ADR 07's upgrade path).
3. **Downstream invalidation**: when clustering is re-run, mark
   `cluster_profiles`, `cluster_comparison`, `anomaly_detection`,
   `recommendations`, and both executive stages as stale in the UI until
   regenerated.
4. **Streaming report generation** (Groq supports streaming completions)
   for a more responsive feel on longer reports.
5. **Chart embedding in PDFs** — reuse the existing `core/visualization.py`
   plotting logic to render static images into the PDF alongside the
   narrative text.
6. **Configurable/pluggable LLM provider** if a future need arises to
   support more than Groq (the `call_groq()` seam in ADR 02 makes this a
   contained change).
