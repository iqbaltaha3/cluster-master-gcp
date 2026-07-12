# ADR 02: Use Groq instead of Anthropic for report generation

**Status:** Accepted
**Date:** Step 2 of the v2.0 rebuild

## Context
v1 called the Anthropic API directly (`llm/report_generator.py`,
`ANTHROPIC_API_KEY`). The product decision for v2.0 is to standardize on
Groq (OpenAI-compatible chat completions API, fast inference, generous
free tier for prototyping) as the sole LLM provider for narrative report
generation.

## Decision
- All LLM calls go through one function: `backend/llm_client.py:call_groq()`.
- Model is configurable via `GROQ_MODEL` env var, defaulting to
  `llama-3.3-70b-versatile`.
- No agent, route, or utility calls the Groq SDK directly — everything
  goes through `call_groq()`. This keeps a provider swap (or a multi-
  provider setup later) to a single-file change.

## Consequences
- One dependency (`groq`) instead of `anthropic`.
- `backend/agents/base.py` and `backend/agents/domain_specialist.py` are
  the only two call sites of `call_groq()` — everything else is prompt
  construction and data prep, which is provider-agnostic.
- If a future requirement needs a specific provider per agent (e.g. a
  cheaper model for the 1-line takeaway extraction), that's a small
  extension to `call_groq()`'s signature, not a rewrite.
