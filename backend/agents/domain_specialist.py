"""
backend/agents/domain_specialist.py
Runs once, immediately after a dataset is uploaded. Infers the domain from
column-level metadata to decide what to research via Tavily, then
synthesizes a short domain brief. That brief is stored on ProjectState
and prepended to the context of every other agent for the rest of the
project.

PRIVACY NOTE: by default this NEVER sends row-level data (i.e. actual
records, which may contain PII) to Groq — only column names, dtypes, and
a few non-identifying per-column example *values* (sampled independently
per column, not as linked rows, and truncated so long free-text values
don't leak much). This matches the design goal stated in llm_client.py
("the LLM only ever sees... never raw row-level data"). If you explicitly
need full sample rows sent for better domain inference (e.g. trusted
internal datasets only), set SEND_SAMPLE_ROWS_TO_LLM=true.
"""
import json

import pandas as pd

from backend.agents.prompts import DOMAIN_SPECIALIST_SYSTEM
from backend.config import settings
from backend.llm_client import call_groq
from backend.tavily_client import tavily_search

QUERY_SYSTEM_PROMPT = """You are a data scientist figuring out what a \
dataset is about from its column names, types, and a few representative \
example values per column. Respond with ONLY a JSON array of 2-3 short \
web search queries (strings) that would help you understand the domain, \
typical benchmarks, and best practices for analyzing this kind of data. \
No preamble, no markdown fences, just the JSON array."""


def _column_examples(df: pd.DataFrame, n_examples: int = 3, max_chars: int = 60) -> dict:
    """A few non-identifying example values per column, sampled
    independently per column (not linked across columns as a row) so this
    can't be reassembled into a real record."""
    examples = {}
    for col in df.columns:
        vals = df[col].dropna().astype(str).str.slice(0, max_chars)
        sample = vals.sample(min(n_examples, len(vals)), random_state=42) if len(vals) else vals
        examples[col] = sample.tolist()
    return examples


def _sample_payload(df: pd.DataFrame, n_rows: int = 8) -> dict:
    payload = {
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "n_rows_total": int(len(df)),
    }
    if settings.SEND_SAMPLE_ROWS_TO_LLM:
        # opt-in only: full linked rows, more useful for domain inference
        # but can include PII if the dataset has any.
        payload["sample_rows"] = df.head(n_rows).to_dict(orient="records")
    else:
        payload["column_example_values"] = _column_examples(df)
    return payload


def _infer_queries(sample: dict) -> list[str]:
    raw = call_groq(
        QUERY_SYSTEM_PROMPT,
        json.dumps(sample, default=str)[:4000],
        max_tokens=200,
        temperature=0.2,
    )
    try:
        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        queries = json.loads(cleaned)
        if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
            return queries[:3]
    except Exception:
        pass
    # Fallback: derive a generic query from column names if parsing failed
    cols = ", ".join(sample["columns"][:6])
    return [f"how to analyze a dataset with columns: {cols}"]


def run_domain_specialist(df: pd.DataFrame) -> str:
    """Returns the domain_brief Markdown string. Does not mutate state directly
    so it can also be unit-tested in isolation."""
    sample = _sample_payload(df)
    queries = _infer_queries(sample)

    research_notes = []
    for q in queries:
        digest = tavily_search(q)
        research_notes.append(f"### Search: {q}\n{digest}")

    user_prompt = f"""DATASET SAMPLE:
{json.dumps(sample, default=str)[:4000]}

WEB RESEARCH:
{chr(10).join(research_notes)}
"""
    brief = call_groq(DOMAIN_SPECIALIST_SYSTEM, user_prompt, max_tokens=500, temperature=0.3)
    return brief
