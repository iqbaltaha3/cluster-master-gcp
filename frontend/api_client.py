"""
frontend/api_client.py
Every HTTP call to the backend lives here. app.py never builds a URL or
parses a response body directly — this keeps the Streamlit file purely
about layout and interaction.
"""
import os
import requests

API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "")  # must match the backend's API_KEY once set
TIMEOUT = 120  # LLM + Tavily calls can take a little while

_session = requests.Session()
if API_KEY:
    _session.headers.update({"X-API-Key": API_KEY})


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


def _raise_for_status(resp):
    if not resp.ok:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise ApiError(detail, status_code=resp.status_code)


def create_session() -> str:
    resp = _session.post(f"{API_BASE}/session", timeout=TIMEOUT)
    _raise_for_status(resp)
    return resp.json()["session_id"]


def upload_dataset(session_id: str, file) -> dict:
    files = {"file": (file.name, file.getvalue())}
    resp = _session.post(f"{API_BASE}/session/{session_id}/upload", files=files, timeout=TIMEOUT)
    _raise_for_status(resp)
    return resp.json()


def get_domain_brief(session_id: str) -> str:
    resp = _session.get(f"{API_BASE}/session/{session_id}/domain-brief", timeout=TIMEOUT)
    _raise_for_status(resp)
    return resp.json()["domain_brief"]


def generate_report(session_id: str, stage: str, payload: dict = None) -> dict:
    """Returns the full backend response: {"stage", "markdown", "stats"}.
    `stats` holds the real computed numbers behind the narrative (tables,
    metrics, chart data) — the frontend renders those directly instead of
    only showing the LLM's prose."""
    resp = _session.post(
        f"{API_BASE}/session/{session_id}/report/{stage}", json=payload or {}, timeout=TIMEOUT
    )
    _raise_for_status(resp)
    return resp.json()


def get_cached_report(session_id: str, stage: str) -> dict | None:
    resp = _session.get(f"{API_BASE}/session/{session_id}/report/{stage}", timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    _raise_for_status(resp)
    return resp.json()


def download_clustered_csv(session_id: str, cluster_id: int = None) -> bytes:
    """Full (cleaned) dataset with a cluster column, or just one cluster's
    rows if cluster_id is given — ready to hand to a download button."""
    params = {"cluster_id": cluster_id} if cluster_id is not None else {}
    resp = _session.get(
        f"{API_BASE}/session/{session_id}/export/clustered_data", params=params, timeout=TIMEOUT
    )
    _raise_for_status(resp)
    return resp.content


def download_pdf(session_id: str, upto_stage: str) -> bytes:
    resp = _session.get(
        f"{API_BASE}/session/{session_id}/pdf", params={"upto": upto_stage}, timeout=TIMEOUT
    )
    _raise_for_status(resp)
    return resp.content
