"""
backend/main.py
FastAPI application. This is the ONLY place that owns state, computes
statistics, and calls the LLM. The Streamlit frontend is a pure client of
this API — it never sees raw JSON, only session ids and Markdown strings.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""
import io
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd

from backend.config import settings
from backend.state import get_store, STAGE_ORDER
from backend.schemas import (
    SessionCreateResponse, UploadResponse, ReportResponse,
    ClusteringRequest, ClusterComparisonRequest,
)
from backend.core import data_loader
from backend import pipeline
from backend.pdf.exporter import build_pdf
from backend.utils import to_jsonable, safe_download_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clustermaster")


def require_api_key(x_api_key: str = Header(default="")):
    """No-op if API_KEY is unset (local/dev). Once set, every request must
    carry a matching X-API-Key header. This is a shared-secret gate, not
    per-user auth — session_id ownership isn't otherwise enforced, so this
    is what keeps the API from being wide open to the public internet."""
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


app = FastAPI(title="ClusterMaster API", version="2.0", dependencies=[Depends(require_api_key)])

app.add_middleware(
    CORSMiddleware,
    # Comma-separated allow-list via ALLOWED_ORIGINS env var. Defaults to
    # "*" only for local/dev convenience — set it explicitly to the
    # frontend's real origin(s) in any deployed environment.
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = get_store(settings.SESSION_TTL_SECONDS)


def _get_state(session_id: str):
    try:
        return store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown or expired session_id")


def _stats_for(state, stage_key: str) -> dict:
    """The raw computed numbers for a stage, sanitized to plain JSON types.
    pipeline.run_* already stashes these on state.stats[stage_key] — this
    just makes them safe to hand back over the wire."""
    return to_jsonable(state.stats.get(stage_key, {}))


def _wrap_stage_errors(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except pipeline.StageError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        # e.g. missing GROQ_API_KEY / TAVILY_API_KEY
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Log full detail server-side, but don't hand internal exception
        # text (stack internals, library error strings) back to the client.
        logger.exception("Unhandled error in stage function %s", getattr(fn, "__name__", fn))
        raise HTTPException(status_code=500, detail="Internal error while processing this stage.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/session", response_model=SessionCreateResponse)
def create_session():
    state = store.create()
    return SessionCreateResponse(session_id=state.session_id)


@app.post("/session/{session_id}/upload", response_model=UploadResponse)
def upload_dataset(session_id: str, file: UploadFile = File(...)):
    state = _get_state(session_id)

    contents = file.file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")

    try:
        df = data_loader.load_dataset(io.BytesIO(contents), filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    state.df = df
    state.dataset_name = file.filename
    # reset any previous pipeline results for this session
    state.cleaned_df = None
    state.stats = {}
    state.project_memory = {}
    state.reports = {}
    state.labels = None
    state.X = None

    domain_brief = _wrap_stage_errors(pipeline.run_domain_brief, state)

    return UploadResponse(
        dataset_name=file.filename,
        n_rows=len(df),
        n_columns=len(df.columns),
        columns=list(df.columns),
        domain_brief=domain_brief,
    )


@app.get("/session/{session_id}/domain-brief")
def get_domain_brief(session_id: str):
    state = _get_state(session_id)
    return {"domain_brief": state.domain_brief}


@app.post("/session/{session_id}/report/data_health", response_model=ReportResponse)
def report_data_health(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_data_health, state)
    return ReportResponse(stage="data_health", markdown=md, stats=_stats_for(state, "data_health"))


@app.post("/session/{session_id}/report/eda", response_model=ReportResponse)
def report_eda(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_eda, state)
    return ReportResponse(stage="eda", markdown=md, stats=_stats_for(state, "eda"))


@app.post("/session/{session_id}/report/clustering", response_model=ReportResponse)
def report_clustering(session_id: str, req: ClusteringRequest):
    state = _get_state(session_id)
    params = {"n_clusters": req.n_clusters, "eps": req.eps, "min_samples": req.min_samples}
    md = _wrap_stage_errors(pipeline.run_clustering, state, algorithm=req.algorithm, **params)
    return ReportResponse(stage="clustering", markdown=md, stats=_stats_for(state, "clustering"))


@app.post("/session/{session_id}/report/cluster_profiles", response_model=ReportResponse)
def report_cluster_profiles(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_cluster_profiles, state)
    return ReportResponse(stage="cluster_profiles", markdown=md, stats=_stats_for(state, "cluster_profiles"))


@app.post("/session/{session_id}/report/cluster_comparison", response_model=ReportResponse)
def report_cluster_comparison(session_id: str, req: ClusterComparisonRequest):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_cluster_comparison, state, req.cluster_a, req.cluster_b)
    return ReportResponse(stage="cluster_comparison", markdown=md, stats=_stats_for(state, "cluster_comparison"))


@app.post("/session/{session_id}/report/anomaly_detection", response_model=ReportResponse)
def report_anomaly_detection(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_anomaly_detection, state)
    return ReportResponse(stage="anomaly_detection", markdown=md, stats=_stats_for(state, "anomaly_detection"))


@app.post("/session/{session_id}/report/recommendations", response_model=ReportResponse)
def report_recommendations(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_recommendations, state)
    return ReportResponse(stage="recommendations", markdown=md, stats=_stats_for(state, "recommendations"))


@app.post("/session/{session_id}/report/executive_dashboard", response_model=ReportResponse)
def report_executive_dashboard(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_executive_dashboard, state)
    return ReportResponse(stage="executive_dashboard", markdown=md, stats=_stats_for(state, "executive_dashboard"))


@app.post("/session/{session_id}/report/executive_report", response_model=ReportResponse)
def report_executive_report(session_id: str):
    state = _get_state(session_id)
    md = _wrap_stage_errors(pipeline.run_executive_report, state)
    return ReportResponse(stage="executive_report", markdown=md, stats=_stats_for(state, "executive_report"))


@app.get("/session/{session_id}/report/{stage}", response_model=ReportResponse)
def get_cached_report(session_id: str, stage: str):
    state = _get_state(session_id)
    if stage not in state.reports:
        raise HTTPException(status_code=404, detail=f"No report generated yet for stage '{stage}'")
    return ReportResponse(stage=stage, markdown=state.reports[stage], stats=_stats_for(state, stage))


@app.get("/session/{session_id}/export/clustered_data")
def export_clustered_data(session_id: str, cluster_id: int = None):
    """Every row of the (cleaned) dataset with its assigned cluster, as a
    downloadable CSV. Pass ?cluster_id=N to get only that segment's rows."""
    state = _get_state(session_id)
    if state.labels is None or state.cleaned_df is None:
        raise HTTPException(status_code=409, detail="Run clustering first.")

    df = state.cleaned_df.copy()
    df.insert(0, "cluster", state.labels)

    if cluster_id is not None:
        df = df[df["cluster"] == cluster_id]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No rows found for cluster {cluster_id}")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    base_name = safe_download_filename((state.dataset_name or "clustermaster").rsplit(".", 1)[0])
    suffix = f"_cluster_{cluster_id}" if cluster_id is not None else "_all_clusters"
    filename = f"{base_name}{suffix}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/session/{session_id}/pdf")
def download_pdf(session_id: str, upto: str):
    state = _get_state(session_id)
    if upto not in STAGE_ORDER:
        raise HTTPException(status_code=400, detail=f"Unknown stage '{upto}'")
    if not state.reports:
        raise HTTPException(status_code=409, detail="No reports generated yet")

    pdf_bytes = _wrap_stage_errors(build_pdf, state, upto)
    base_name = safe_download_filename(state.dataset_name or "clustermaster")
    filename = f"{base_name}_{upto}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )