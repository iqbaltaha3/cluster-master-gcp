"""
backend/config.py
Central configuration. All secrets come from environment variables loaded
from a .env file — never from request bodies, never from the frontend.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from project root if present


class Settings:
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")

    # session store TTL (seconds) — in-memory sessions are cleared after this
    SESSION_TTL_SECONDS: int = int(os.environ.get("SESSION_TTL_SECONDS", 3600 * 6))

    # safety caps
    MAX_UPLOAD_MB: int = int(os.environ.get("MAX_UPLOAD_MB", 50))
    LLM_MAX_CONTEXT_CHARS: int = int(os.environ.get("LLM_MAX_CONTEXT_CHARS", 8000))

    # comma-separated list of allowed browser origins for CORS, e.g.
    # "https://clustermaster-frontend-xyz.a.run.app,http://localhost:8501"
    # Falls back to "*" only if explicitly left unset (local/dev convenience) —
    # set this explicitly to the frontend's real origin(s) in any deployment.
    ALLOWED_ORIGINS: str = os.environ.get("ALLOWED_ORIGINS", "*")

    # Shared secret the frontend must send as `X-API-Key` on every request.
    # This is NOT per-user auth — it just stops the API from being open to
    # the entire internet when CORS is relaxed (e.g. during setup). Leave
    # unset locally; always set it in any publicly reachable deployment.
    API_KEY: str = os.environ.get("API_KEY", "")

    # Opt-in only: sends full linked sample rows (not just per-column
    # example values) to Groq during domain inference. Leave false unless
    # you're certain uploaded datasets won't contain PII you don't want
    # leaving your infra.
    SEND_SAMPLE_ROWS_TO_LLM: bool = os.environ.get("SEND_SAMPLE_ROWS_TO_LLM", "false").lower() == "true"


    @property
    def allowed_origins_list(self) -> list[str]:
        raw = self.ALLOWED_ORIGINS.strip()
        if raw == "*" or not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()


def require_groq_key():
    if not settings.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Create a .env file (see .env.example) "
            "with GROQ_API_KEY=your_key_here."
        )


def require_tavily_key():
    if not settings.TAVILY_API_KEY:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Create a .env file (see .env.example) "
            "with TAVILY_API_KEY=your_key_here."
        )
