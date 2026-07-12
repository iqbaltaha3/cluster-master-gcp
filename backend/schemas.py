"""
backend/schemas.py
Pydantic request/response models. Keeping these separate from routes
makes the API contract easy to scan in one place.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    session_id: str


class UploadResponse(BaseModel):
    dataset_name: str
    n_rows: int
    n_columns: int
    columns: list[str]
    domain_brief: str


class ReportResponse(BaseModel):
    stage: str
    markdown: str
    # Raw computed numbers behind the narrative (tables, metrics, chart data)
    # so the frontend can show the person real data, not just LLM prose.
    # Typed as Any (not dict) because some stages — e.g. recommendations —
    # store a list, not a dict, in state.stats[stage_key].
    stats: Any = Field(default_factory=dict)


class ClusteringRequest(BaseModel):
    algorithm: str = "KMeans"  # one of: KMeans, Gaussian Mixture (GMM), Agglomerative, DBSCAN
    n_clusters: Optional[int] = 5
    eps: Optional[float] = 0.5
    min_samples: Optional[int] = 5


class ClusterComparisonRequest(BaseModel):
    cluster_a: int
    cluster_b: int


class ErrorResponse(BaseModel):
    detail: str