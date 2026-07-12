"""
backend/pipeline.py
One function per pipeline stage. Each function:
  1. Computes statistics using the existing core/analytics modules
     (unchanged logic from the original project).
  2. Stores anything needed by later stages on ProjectState.
  3. Calls run_agent() to turn those statistics into a narrative report.
Routes in main.py just call these and return the report text.
"""
from backend.agents.base import run_agent
from backend.agents.domain_specialist import run_domain_specialist
from backend.state import ProjectState

import numpy as np

from backend.core import preprocessing, clustering as core_clustering, evaluation, reduction
from backend.analytics import (
    data_health as ah,
    eda as eda_mod,
    cluster_profiler,
    cluster_comparison as cc_mod,
    anomaly_detection,
    recommendation_engine,
)


class StageError(Exception):
    pass


def run_domain_brief(state: ProjectState) -> str:
    state.domain_brief = run_domain_specialist(state.df)
    return state.domain_brief


def run_data_health(state: ProjectState) -> str:
    stats = ah.compute_data_health(state.df)
    cleaned_df, cleaning_report = preprocessing.clean_dataset(state.df)
    state.cleaned_df = cleaned_df
    stats["cleaning_actions"] = cleaning_report
    numeric_cols, categorical_cols, _ = preprocessing.get_column_types(cleaned_df)
    state.numeric_cols, state.categorical_cols = numeric_cols, categorical_cols
    return run_agent(state, "data_health", stats)


def run_eda(state: ProjectState) -> str:
    if state.cleaned_df is None:
        raise StageError("Run Data Health first.")
    df = state.cleaned_df
    stats = {
        "summary_statistics": eda_mod.compute_summary_statistics(df, state.numeric_cols),
        "pca_variance": eda_mod.compute_pca_variance(df, state.numeric_cols),
        "top_correlations": eda_mod.top_correlations(df, state.numeric_cols),
        "unusual_distributions": eda_mod.unusual_distributions(df, state.numeric_cols),
    }
    return run_agent(state, "eda", stats)


def run_clustering(state: ProjectState, algorithm: str = "KMeans", **params) -> str:
    if state.cleaned_df is None:
        raise StageError("Run Data Health first.")
    selected_columns = state.numeric_cols + state.categorical_cols
    try:
        X, feature_names, _ = preprocessing.build_feature_matrix(state.cleaned_df, selected_columns)
    except ValueError as e:
        # e.g. every selected column was dropped as constant / no usable columns
        raise StageError(f"Can't cluster this dataset: {e}")

    n_rows = X.shape[0]
    n_clusters_requested = params.get("n_clusters")
    if algorithm in ("KMeans", "Gaussian Mixture (GMM)", "Agglomerative") and n_clusters_requested:
        if n_clusters_requested > n_rows:
            raise StageError(
                f"Requested {n_clusters_requested} clusters but only {n_rows} rows are available "
                f"after cleaning. Choose a smaller number of clusters."
            )

    try:
        labels, model, info = core_clustering.run_clustering(X, algorithm, **params)
    except ValueError as e:
        raise StageError(f"Clustering failed with the chosen parameters: {e}")

    metrics = evaluation.evaluate_clustering(X, labels)

    state.X = X
    state.feature_names = feature_names
    state.labels = labels
    state.clustering_info = info

    # 2D projection for a real scatter chart on the frontend (previously
    # computed nowhere — core/reduction.py existed but was never called).
    # Sample down for very large datasets so the response stays light.
    coords, explained_variance = reduction.reduce_pca(X, n_components=2)
    max_points = 2000
    if len(coords) > max_points:
        idx = np.random.RandomState(42).choice(len(coords), max_points, replace=False)
    else:
        idx = np.arange(len(coords))
    scatter_2d = {
        "x": coords[idx, 0].round(4).tolist(),
        "y": coords[idx, 1].round(4).tolist(),
        "cluster": [int(c) for c in labels[idx]],
        "pca_explained_variance": [round(float(v), 4) for v in explained_variance],
    }

    stats = {
        **info,
        "cluster_sizes": {int(k): int((labels == k).sum()) for k in set(labels)},
        "evaluation_metrics": metrics,
        "scatter_2d": scatter_2d,
    }
    return run_agent(state, "clustering", stats)


def run_cluster_profiles(state: ProjectState) -> str:
    if state.labels is None:
        raise StageError("Run Clustering first.")
    profiles = cluster_profiler.profile_clusters(
        state.cleaned_df, state.labels, state.numeric_cols, state.categorical_cols
    )
    state.stats["cluster_profiles_raw"] = profiles
    return run_agent(state, "cluster_profiles", profiles)


def run_cluster_comparison(state: ProjectState, cluster_a: int, cluster_b: int) -> str:
    if state.labels is None:
        raise StageError("Run Clustering first.")
    valid_ids = set(int(v) for v in state.labels)
    missing = [cid for cid in (cluster_a, cluster_b) if cid not in valid_ids]
    if missing:
        raise StageError(
            f"Cluster id(s) {missing} don't exist in the current clustering. "
            f"Valid cluster ids: {sorted(valid_ids)}."
        )
    if cluster_a == cluster_b:
        raise StageError("Choose two different clusters to compare.")
    stats = cc_mod.compare_clusters(
        state.cleaned_df, state.labels, cluster_a, cluster_b, state.numeric_cols, state.categorical_cols
    )
    return run_agent(state, "cluster_comparison", stats)


def run_anomaly_detection(state: ProjectState) -> str:
    if state.X is None:
        raise StageError("Run Clustering first (feature matrix is reused).")
    stats = anomaly_detection.detect_anomalies(state.X, state.cleaned_df)
    return run_agent(state, "anomaly_detection", stats)


def run_recommendations(state: ProjectState) -> str:
    profiles = state.stats.get("cluster_profiles_raw")
    if profiles is None:
        raise StageError("Run Cluster Profiles first.")
    stats = recommendation_engine.generate_recommendations(profiles)
    return run_agent(state, "recommendations", stats)


def run_executive_dashboard(state: ProjectState) -> str:
    stats = {
        "data_health": state.stats.get("data_health"),
        "clustering": state.stats.get("clustering"),
        "cluster_profiles": state.stats.get("cluster_profiles_raw"),
    }
    return run_agent(state, "executive_dashboard", stats, max_tokens=500)


def run_executive_report(state: ProjectState) -> str:
    # Deliberately pass an empty stats dict — the Executive should synthesize
    # PRIOR FINDINGS (project_memory), not re-derive numbers.
    return run_agent(state, "executive_report", {}, max_tokens=900)