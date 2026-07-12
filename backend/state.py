"""
backend/state.py
In-memory project state, one ProjectState per session_id.

This is the single shared scratchpad every agent reads from and writes to.
No JSON is ever handed to the frontend directly from here — routes in
main.py decide exactly what subset (usually just a Markdown string) goes
out over the wire.

NOTE ON PERSISTENCE: this is an in-memory store, so state is lost on
backend restart and does not scale across multiple worker processes.
That's an intentional simplification for v1 — see
docs/07-state-persistence-tradeoff.md for the reasoning and the upgrade
path (Redis / a database-backed session) if this needs to run with
multiple workers or survive restarts.
"""
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import pandas as pd

STAGE_ORDER = [
    "data_health",
    "eda",
    "clustering",
    "cluster_profiles",
    "cluster_comparison",
    "anomaly_detection",
    "recommendations",
    "executive_dashboard",
    "executive_report",
]


@dataclass
class ProjectState:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    dataset_name: str = ""
    df: Optional[pd.DataFrame] = None
    cleaned_df: Optional[pd.DataFrame] = None
    numeric_cols: list = field(default_factory=list)
    categorical_cols: list = field(default_factory=list)

    X: object = None
    feature_names: list = field(default_factory=list)
    labels: object = None
    clustering_info: dict = field(default_factory=dict)

    # written once at upload time by the Domain Specialist agent
    domain_brief: str = ""

    # raw computed statistics per stage — backend-only, never sent verbatim
    # to the frontend or included wholesale in a response
    stats: dict = field(default_factory=dict)

    # 1-2 sentence takeaway per stage, written by each agent after it runs,
    # read by every later agent so context accumulates down the pipeline
    project_memory: dict = field(default_factory=dict)

    # finished Markdown reports per stage — this IS what the frontend gets
    reports: dict = field(default_factory=dict)


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600 * 6):
        self._sessions: dict[str, ProjectState] = {}
        self._lock = Lock()
        self.ttl_seconds = ttl_seconds

    def create(self) -> ProjectState:
        sid = str(uuid.uuid4())
        with self._lock:
            self._sessions[sid] = ProjectState(session_id=sid)
        return self._sessions[sid]

    def get(self, session_id: str) -> ProjectState:
        self._evict_expired()
        with self._lock:
            state = self._sessions.get(session_id)
        if state is None:
            raise KeyError(f"Unknown or expired session_id: {session_id}")
        state.last_used = time.time()
        return state

    def _evict_expired(self):
        now = time.time()
        with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s.last_used > self.ttl_seconds
            ]
            for sid in expired:
                del self._sessions[sid]


# module-level singleton, imported by main.py and agents
store: SessionStore | None = None


def get_store(ttl_seconds: int) -> SessionStore:
    global store
    if store is None:
        store = SessionStore(ttl_seconds=ttl_seconds)
    return store
