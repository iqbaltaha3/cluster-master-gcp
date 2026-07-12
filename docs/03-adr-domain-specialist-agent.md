# ADR 03: A Domain Specialist agent runs once, before every other agent

**Status:** Accepted
**Date:** Step 3 of the v2.0 rebuild

## Context
Each of the 9 pipeline stages (Data Health, EDA, Clustering, ... Executive
Report) is written by a distinct agent, each with a narrow view of the
data (only the statistics relevant to its own stage). None of them know
*what kind of dataset* they're looking at — a "spending score" column
means something different in retail vs. SaaS vs. healthcare data, and an
agent with no domain grounding tends to write generic, hedge-everything
prose.

## Decision
Add one agent that runs exactly once, immediately after upload:
1. Take only the column names, dtypes, and ~8 sample rows (never the full
   dataset — keeps the call cheap and limits exposure of raw data to a
   third-party search).
2. Ask Groq to propose 2-3 web search queries that would help understand
   this domain.
3. Run those queries through Tavily.
4. Synthesize a short (<300 word) Markdown "domain brief": likely domain,
   typical benchmarks/patterns, what a good analyst focuses on here.
5. Store the brief on `ProjectState.domain_brief`.

Every other agent's prompt (`backend/agents/base.py:run_agent`) prepends
this brief before its own stage-specific statistics. No agent-specific
code is needed to consume it — it's just always in the context.

## Consequences
- One extra LLM call + a few Tavily calls per new dataset upload, not per
  report generation — this cost is paid once, not 9 times.
- All 9 downstream agents get grounded, domain-aware framing for free,
  without needing their own research capability.
- If Tavily is not configured (`TAVILY_API_KEY` missing), the search step
  degrades to "(search failed for '...')" text per query rather than
  crashing the upload — the brief will just be less specific, not absent.
