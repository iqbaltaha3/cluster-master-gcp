"""
backend/agents/base.py
Every stage agent (data_health, eda, clustering, ...) is just a call to
run_agent() with that stage's freshly computed statistics. This keeps the
9 agent files nearly identical and easy to read.
"""
import json

from backend.agents.prompts import STAGE_PROMPTS, STAGE_LABELS
from backend.llm_client import call_groq
from backend.state import ProjectState


def _json_safe(data: dict, max_chars: int) -> str:
    text = json.dumps(data, default=str, indent=2)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n... (truncated for brevity)"
    return text


def _format_prior_findings(project_memory: dict) -> str:
    if not project_memory:
        return "(none yet — this is the first analytical stage)"
    lines = [f"- {STAGE_LABELS.get(k, k)}: {v}" for k, v in project_memory.items()]
    return "\n".join(lines)


def _extract_takeaway(report_md: str) -> str:
    """Cheap, no extra LLM call: use the first non-empty line as the takeaway."""
    for line in report_md.splitlines():
        clean = line.strip("# ").strip()
        if clean:
            return clean[:220]
    return "(no summary available)"


def run_agent(state: ProjectState, stage_key: str, stats: dict, max_tokens: int = 900) -> str:
    system_prompt = STAGE_PROMPTS[stage_key]

    user_prompt = f"""DOMAIN BRIEF:
{state.domain_brief or "(no domain brief available)"}

PRIOR FINDINGS:
{_format_prior_findings(state.project_memory)}

THIS STAGE'S DATA:
{_json_safe(stats, max_chars=8000)}
"""

    report_md = call_groq(system_prompt, user_prompt, max_tokens=max_tokens, temperature=0.65)

    state.stats[stage_key] = stats
    state.reports[stage_key] = report_md
    state.project_memory[stage_key] = _extract_takeaway(report_md)
    return report_md