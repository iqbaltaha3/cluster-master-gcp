"""
backend/llm_client.py
Thin wrapper around the Groq API. This is the ONLY place in the codebase
that talks to Groq — every agent calls call_groq(), nothing else.

Design goal (unchanged from the original project): the LLM only ever sees
JSON summaries / Markdown context that we've deliberately built for it,
never raw row-level data.
"""
from groq import Groq

from backend.config import settings, require_groq_key

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    require_groq_key()
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 900, temperature: float = 0.4) -> str:
    """Single non-streaming chat completion. Returns plain text (Markdown)."""
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()
