"""
frontend/app.py
ClusterMaster — Streamlit frontend.
REDESIGN v5.0 — White & Red theme with 3D depth.
All backend logic & API contracts preserved.
"""
import io

import pandas as pd
import streamlit as st

import api_client as api

# ---------------------------------------------------------------------------
# 1. GLOBAL DESIGN SYSTEM INJECTION (White & Red Theme)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="ClusterMaster", page_icon="🧭", layout="wide")

DESIGN_CSS = """
<style>
/* ----- Design Tokens (White & Red with 3D depth) ----- */
:root {
  --color-primary: #DC2626;           /* Bold Red */
  --color-primary-hover: #B91C1C;
  --color-primary-light: #FEE2E2;
  --color-primary-dark: #991B1B;
  --color-secondary: #16A34A;         /* Green for positive deltas */
  --color-bg: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-border: #E5E7EB;
  --color-text-primary: #111827;
  --color-text-secondary: #4B5563;
  --color-text-muted: #9CA3AF;
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-2xl: 1.9rem;
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 30px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.04);
  --shadow-3d: 0 8px 0 #D1D5DB, 0 10px 20px rgba(0,0,0,0.10);
}

/* ----- Base Reset & Typography ----- */
html, body, .stApp {
  font-family: var(--font-family);
  background-color: var(--color-bg) !important;
  color: var(--color-text-primary);
  font-weight: 450;
  -webkit-font-smoothing: antialiased;
}

.main .block-container {
  padding-top: var(--space-lg) !important;
  padding-bottom: var(--space-2xl) !important;
  padding-left: var(--space-xl) !important;
  padding-right: var(--space-xl) !important;
  max-width: 1280px !important;
}

/* ----- Sidebar (white, clean) ----- */
section[data-testid="stSidebar"] {
  background: var(--color-surface) !important;
  border-right: 1px solid var(--color-border) !important;
  padding: var(--space-lg) var(--space-md) !important;
  box-shadow: 4px 0 20px rgba(0,0,0,0.04);
}

/* All sidebar text dark for readability */
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown div,
section[data-testid="stSidebar"] label {
  color: var(--color-text-primary) !important;
}

/* Sidebar navigation radio buttons — dark text, subtle border */
section[data-testid="stSidebar"] div[role="radiogroup"] {
  gap: var(--space-sm);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: var(--space-sm) var(--space-md) !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary) !important;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {
  background: var(--color-primary) !important;
  color: white !important;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md), inset 0 -3px 0 var(--color-primary-dark);
  transform: scale(1.02);
}

/* ----- Metric Cards (white, 3D shadow) ----- */
div[data-testid="stMetric"] {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg) !important;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}
div[data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg), 0 8px 0 var(--color-border);
}
div[data-testid="stMetricLabel"] {
  font-size: var(--font-size-xs) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-secondary) !important;
}
div[data-testid="stMetricValue"] {
  font-size: var(--font-size-xl) !important;
  font-weight: 700 !important;
  color: var(--color-text-primary) !important;
  letter-spacing: -0.02em;
}
div[data-testid="stMetricDelta"] > span {
  color: var(--color-secondary) !important;
}

/* ----- Buttons (red primary, 3D) ----- */
.stButton > button {
  min-height: 44px !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  font-size: var(--font-size-sm) !important;
  padding: 0 var(--space-lg) !important;
  border: 1px solid var(--color-border) !important;
  background: var(--color-surface) !important;
  color: var(--color-text-primary) !important;
  box-shadow: var(--shadow-sm);
  transition: all 0.1s ease;
}
.stButton > button:hover {
  background: var(--color-bg) !important;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.stButton > button:active {
  transform: translateY(2px);
  box-shadow: var(--shadow-sm);
}
.stButton > button[kind="primary"] {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: white !important;
  box-shadow: 0 4px 0 var(--color-primary-dark), var(--shadow-sm);
}
.stButton > button[kind="primary"]:hover {
  background: var(--color-primary-hover) !important;
  border-color: var(--color-primary-hover) !important;
  box-shadow: 0 6px 0 var(--color-primary-dark), var(--shadow-md);
  transform: translateY(-2px);
}
.stButton > button[kind="primary"]:active {
  transform: translateY(4px);
  box-shadow: 0 2px 0 var(--color-primary-dark), var(--shadow-sm);
}

/* ----- DataFrames (light theme) ----- */
div[data-testid="stDataFrame"] {
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  overflow: hidden;
  background: var(--color-surface);
}
div[data-testid="stDataFrame"] thead tr th {
  background: var(--color-bg) !important;
  font-weight: 600 !important;
  font-size: var(--font-size-xs) !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary) !important;
  padding: var(--space-sm) var(--space-md) !important;
  border-bottom: 2px solid var(--color-primary);
}
div[data-testid="stDataFrame"] tbody td {
  color: var(--color-text-primary);
}

/* ----- Insight Card (white, red accent) ----- */
.insight-card {
  background: var(--color-surface);
  border-left: 6px solid var(--color-primary);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  padding: var(--space-lg) var(--space-xl);
  box-shadow: var(--shadow-sm);
  margin-top: var(--space-lg);
}
.insight-card h1, .insight-card h2, .insight-card h3 {
  margin-top: var(--space-md);
  margin-bottom: var(--space-sm);
  font-weight: 700;
  color: var(--color-text-primary);
}
.insight-card p, .insight-card li {
  color: var(--color-text-secondary);
  line-height: 1.7;
}

/* ----- Progress Bar (red) ----- */
.custom-progress {
  height: 6px;
  background: var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: var(--space-lg);
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}
.custom-progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 6px;
  transition: width 0.3s ease;
}

/* ----- Expanders & alerts ----- */
.streamlit-expanderHeader {
  font-weight: 600 !important;
  color: var(--color-text-primary) !important;
}
.stAlert {
  border-radius: var(--radius-md) !important;
  border-left: 4px solid var(--color-primary) !important;
  background: var(--color-primary-light) !important;
}

/* ----- Download buttons (green, 3D) ----- */
.stDownloadButton > button {
  background: var(--color-secondary) !important;
  border-color: var(--color-secondary) !important;
  color: white !important;
  box-shadow: 0 4px 0 #15803D, var(--shadow-sm);
}
.stDownloadButton > button:hover {
  background: #15803D !important;
  border-color: #15803D !important;
  box-shadow: 0 6px 0 #15803D, var(--shadow-md);
  transform: translateY(-2px);
}
.stDownloadButton > button:active {
  transform: translateY(4px);
  box-shadow: 0 2px 0 #15803D, var(--shadow-sm);
}

/* ----- Responsive ----- */
@media (max-width: 768px) {
  .main .block-container {
    padding-left: var(--space-md) !important;
    padding-right: var(--space-md) !important;
  }
  div[data-testid="stMetric"] {
    padding: var(--space-sm) var(--space-md) !important;
  }
}
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. APP CONFIG & SESSION STATE (UNCHANGED)
# ---------------------------------------------------------------------------
STAGES = [
    ("data_health", "Data Health"),
    ("eda", "Exploratory Analysis"),
    ("clustering", "Clustering"),
    ("cluster_profiles", "Cluster Profiles"),
    ("cluster_comparison", "Cluster Comparison"),
    ("anomaly_detection", "Anomaly Detection"),
    ("recommendations", "Business Recommendations"),
    ("executive_dashboard", "Executive Dashboard"),
    ("executive_report", "Executive Report"),
]

if "session_id" not in st.session_state:
    try:
        st.session_state.session_id = api.create_session()
    except api.ApiError as e:
        st.error(f"Could not reach the backend: {e}")
        st.stop()

if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False
if "cluster_ready" not in st.session_state:
    st.session_state.cluster_ready = False

def reset_after_upload():
    st.session_state.cluster_ready = False

# ---------------------------------------------------------------------------
# 3. SIDEBAR (REDESIGNED LAYOUT)
# ---------------------------------------------------------------------------
with st.sidebar:
    # Brand
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="font-size: 28px;">🧭</span>
            <span style="font-size: 22px; font-weight: 800; letter-spacing: -0.02em; color: var(--color-text-primary);">ClusterMaster</span>
        </div>
        <p style="font-size: 14px; color: var(--color-text-secondary); margin-top: -4px; margin-bottom: 16px; font-weight: 500;">
            From raw data to actionable intelligence.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Data Upload
    st.markdown("#### Data Source")
    upload = st.file_uploader(
        "Upload dataset",
        type=["csv", "tsv", "xlsx", "xls", "json", "parquet"],
        label_visibility="collapsed"
    )

    if upload is not None and st.session_state.get("last_upload_name") != upload.name:
        with st.spinner("Uploading & researching domain..."):
            try:
                result = api.upload_dataset(st.session_state.session_id, upload)
                st.session_state.dataset_loaded = True
                st.session_state.last_upload_name = upload.name
                st.session_state.domain_brief = result["domain_brief"]
                st.session_state.dataset_info = result
                reset_after_upload()
            except api.ApiError as e:
                st.error(f"Upload failed: {e}")

    if st.session_state.dataset_loaded:
        info = st.session_state.dataset_info
        st.success(f"✅ {info['dataset_name']}  ·  {info['n_rows']} rows × {info['n_columns']} cols")
        with st.expander("🔎 Domain Brief"):
            st.markdown(st.session_state.domain_brief)

    st.markdown("---")

    # Navigation (Progress + Radio)
    current_idx = STAGES.index(next((s for s in STAGES if s[0] == st.session_state.get("active_stage", "data_health")), STAGES[0]))
    total = len(STAGES)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 4px;">
            <span>Progress</span>
            <span>{current_idx + 1} / {total}</span>
        </div>
        <div class="custom-progress">
            <div class="custom-progress-fill" style="width: {((current_idx + 1) / total) * 100}%;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    labels = [title for _, title in STAGES]
    choice = st.radio(
        "Navigate",
        labels,
        index=current_idx,
        label_visibility="collapsed",
        key="stage_radio"
    )
    active_stage = STAGES[labels.index(choice)][0]
    st.session_state["active_stage"] = active_stage

# ---------------------------------------------------------------------------
# 4. CORE HELPERS (PRESERVED LOGIC)
# ---------------------------------------------------------------------------
def require_dataset():
    if not st.session_state.dataset_loaded:
        st.info("👈 Please upload a dataset in the sidebar to begin.")
        st.stop()

def stage_header(title: str, description: str = ""):
    """Renders a clean stage header with title and optional description (no emojis)."""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<h1 style='font-size: 28px; font-weight: 700; margin-bottom: 0; letter-spacing: -0.02em; color: var(--color-text-primary);'>{title}</h1>", unsafe_allow_html=True)
        if description:
            st.markdown(f"<p style='color: var(--color-text-secondary); margin-top: -4px; font-weight: 400;'>{description}</p>", unsafe_allow_html=True)

def _get_clustered_df():
    if "clustered_df" not in st.session_state:
        try:
            csv_bytes = api.download_clustered_csv(st.session_state.session_id)
            st.session_state.clustered_df = pd.read_csv(io.BytesIO(csv_bytes))
        except api.ApiError:
            return None
    return st.session_state.clustered_df

# ---------------------------------------------------------------------------
# 5. STAT RENDERERS (UNCHANGED — PRESERVED AS-IS)
# ---------------------------------------------------------------------------
def render_data_health(stats: dict):
    if not stats: return
    shape = stats.get("shape", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", shape.get("rows", "—"))
    c2.metric("Columns", shape.get("columns", "—"))
    c3.metric("Duplicate rows", stats.get("duplicate_rows", 0))
    c4.metric("Columns with missing data", len(stats.get("missing_values", {})))
    missing = stats.get("missing_values", {})
    if missing:
        st.markdown("**Missing values by column**")
        df = pd.DataFrame([{"column": col, **vals} for col, vals in missing.items()])
        st.dataframe(df, use_container_width=True, hide_index=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if stats.get("constant_columns"):
            st.markdown("**Constant columns** (no variance — safe to drop)")
            st.write(", ".join(stats["constant_columns"]))
        if stats.get("high_cardinality_columns"):
            st.markdown("**High-cardinality columns**")
            st.dataframe(pd.DataFrame(stats["high_cardinality_columns"]), use_container_width=True, hide_index=True)
    with col_b:
        if stats.get("highly_correlated_pairs"):
            st.markdown("**Highly correlated feature pairs**")
            st.dataframe(pd.DataFrame(stats["highly_correlated_pairs"]), use_container_width=True, hide_index=True)
        if stats.get("outlier_counts"):
            st.markdown("**Outlier counts** (IQR method)")
            outlier_df = pd.DataFrame([{"column": c, "outliers": n} for c, n in stats["outlier_counts"].items()])
            st.dataframe(outlier_df, use_container_width=True, hide_index=True)
    cleaning = stats.get("cleaning_actions")
    if cleaning:
        with st.expander("🧹 Cleaning actions applied before downstream stages"):
            st.write(f"Duplicate rows removed: **{cleaning.get('duplicates_removed', 0)}**")
            removed = cleaning.get("constant_columns_removed") or []
            st.write(f"Constant columns removed: **{', '.join(removed) if removed else 'none'}**")

def render_eda(stats: dict):
    if not stats: return
    summary = stats.get("summary_statistics")
    if summary:
        st.markdown("**Summary statistics**")
        df = pd.DataFrame.from_dict(summary, orient="index")
        st.dataframe(df, use_container_width=True)
    col_a, col_b = st.columns(2)
    with col_a:
        pca = stats.get("pca_variance")
        if pca:
            st.markdown("**PCA explained variance**")
            n = len(pca["explained_variance_ratio"])
            chart_df = pd.DataFrame({"explained": pca["explained_variance_ratio"], "cumulative": pca["cumulative_variance"]}, index=[f"PC{i+1}" for i in range(n)])
            st.bar_chart(chart_df)
    with col_b:
        top_corr = stats.get("top_correlations")
        if top_corr:
            st.markdown("**Top correlations**")
            st.dataframe(pd.DataFrame(top_corr), use_container_width=True, hide_index=True)
    unusual = stats.get("unusual_distributions")
    if unusual:
        st.markdown("**Skewed distributions**")
        st.dataframe(pd.DataFrame(unusual), use_container_width=True, hide_index=True)

def render_clustering(stats: dict):
    if not stats: return
    metrics = stats.get("evaluation_metrics", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clusters found", stats.get("n_clusters_found", "—"))
    c2.metric("Noise points", stats.get("n_noise_points", 0))
    sil = metrics.get("silhouette_score")
    c3.metric("Silhouette score", f"{sil:.3f}" if sil is not None else "n/a")
    dbi = metrics.get("davies_bouldin_score")
    c4.metric("Davies–Bouldin", f"{dbi:.3f}" if dbi is not None else "n/a")
    col_a, col_b = st.columns(2)
    with col_a:
        sizes = stats.get("cluster_sizes")
        if sizes:
            st.markdown("**Cluster sizes**")
            size_df = pd.Series({f"Cluster {k}": v for k, v in sizes.items()}).sort_index()
            st.bar_chart(size_df)
    with col_b:
        scatter = stats.get("scatter_2d")
        if scatter:
            st.markdown("**Clusters projected to 2D (PCA)**")
            scatter_df = pd.DataFrame({"PC1": scatter["x"], "PC2": scatter["y"], "cluster": [f"Cluster {c}" for c in scatter["cluster"]]})
            st.scatter_chart(scatter_df, x="PC1", y="PC2", color="cluster")
    clustered_df = _get_clustered_df()
    if clustered_df is not None:
        st.download_button("⬇️ Download full dataset with cluster labels (CSV)", data=clustered_df.to_csv(index=False).encode("utf-8"), file_name="all_clusters.csv", mime="text/csv", key="dl_clustering_tab")

def render_cluster_profiles(stats: dict):
    if not stats: return
    sizes = {cid: p["size"] for cid, p in stats.items()}
    st.markdown("**Cluster sizes**")
    st.bar_chart(pd.Series({f"Cluster {cid}": s for cid, s in sizes.items()}).sort_index())
    clustered_df = _get_clustered_df()
    if clustered_df is not None:
        st.download_button("⬇️ Download full dataset with cluster labels (CSV)", data=clustered_df.to_csv(index=False).encode("utf-8"), file_name="all_clusters.csv", mime="text/csv")
    for cid, profile in stats.items():
        label = f"Cluster {profile['cluster_id']} — {profile['size']} customers ({profile['size_pct']}%)"
        with st.expander(label):
            if clustered_df is not None:
                segment_df = clustered_df[clustered_df["cluster"] == int(cid)]
                st.download_button(f"⬇️ Download this segment's {len(segment_df)} customers (CSV)", data=segment_df.to_csv(index=False).encode("utf-8"), file_name=f"cluster_{cid}_customers.csv", mime="text/csv", key=f"dl_cluster_{cid}")
            numeric_profile = profile.get("numeric_profile", {})
            if numeric_profile:
                st.markdown("Numeric averages vs. overall dataset")
                st.dataframe(pd.DataFrame.from_dict(numeric_profile, orient="index"), use_container_width=True)
            distinguishing = profile.get("distinguishing_features")
            if distinguishing:
                st.markdown("Most distinguishing features (largest deviation from overall average)")
                st.dataframe(pd.DataFrame(distinguishing), use_container_width=True, hide_index=True)
            categorical_profile = profile.get("categorical_profile", {})
            if categorical_profile:
                st.markdown("Dominant categories")
                for col, top_values in categorical_profile.items():
                    st.write(f"**{col}**")
                    st.dataframe(pd.DataFrame(top_values), use_container_width=True, hide_index=True)

def render_cluster_comparison(stats: dict):
    if not stats: return
    a, b = stats.get("cluster_a", {}), stats.get("cluster_b", {})
    c1, c2 = st.columns(2)
    c1.metric(f"Cluster {a.get('id')} size", a.get("size", "—"))
    c2.metric(f"Cluster {b.get('id')} size", b.get("size", "—"))
    diffs = stats.get("numeric_differences")
    if diffs:
        st.markdown("**Numeric differences** (sorted by absolute gap)")
        st.dataframe(pd.DataFrame(diffs), use_container_width=True, hide_index=True)
    cat_diffs = stats.get("categorical_differences", {})
    if cat_diffs:
        st.markdown("**Categorical composition**")
        for col, vals in cat_diffs.items():
            st.write(f"**{col}**")
            colA, colB = st.columns(2)
            with colA:
                st.caption(f"Cluster {a.get('id')}")
                st.dataframe(pd.DataFrame(list(vals.get("cluster_a_top", {}).items()), columns=["value", "share_pct"]), use_container_width=True, hide_index=True)
            with colB:
                st.caption(f"Cluster {b.get('id')}")
                st.dataframe(pd.DataFrame(list(vals.get("cluster_b_top", {}).items()), columns=["value", "share_pct"]), use_container_width=True, hide_index=True)

def render_anomaly_detection(stats: dict):
    if not stats: return
    summary = stats.get("score_summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomalies found", stats.get("n_anomalies", 0))
    c2.metric("% of records", f"{stats.get('pct_anomalies', 0)}%")
    c3.metric("Max anomaly score", summary.get("max", "—"))
    c4.metric("Mean anomaly score", summary.get("mean", "—"))
    top = stats.get("top_anomalies")
    if top:
        st.markdown("**Most anomalous records**")
        st.dataframe(pd.DataFrame(top), use_container_width=True, hide_index=True)

def render_recommendations(stats):
    recs = stats if isinstance(stats, list) else None
    if not recs: return
    st.markdown("**Rule-based recommendations by cluster**")
    st.dataframe(pd.DataFrame(recs), use_container_width=True, hide_index=True)

RENDERERS = {
    "data_health": render_data_health,
    "eda": render_eda,
    "clustering": render_clustering,
    "cluster_profiles": render_cluster_profiles,
    "cluster_comparison": render_cluster_comparison,
    "anomaly_detection": render_anomaly_detection,
    "recommendations": render_recommendations,
}

# ---------------------------------------------------------------------------
# 6. CORE UI CONTROLS (REDESIGNED ACTION BAR + INSIGHT CARD)
# ---------------------------------------------------------------------------
def report_and_pdf_controls(stage_key: str, generate_label: str, payload: dict = None):
    """
    Renders the action bar (Generate + PDF) at the top, then the computed data,
    then the agent narrative as a distinct 'insight' card below.
    Preserves all API calls and session state keys.
    """
    # ---- Action Bar ----
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        if st.session_state.get(f"report_{stage_key}"):
            st.markdown("✅ **Ready** — data loaded & analyzed")
        else:
            st.markdown("⏳ **Awaiting generation**")
    with col2:
        if st.button(generate_label, type="primary", use_container_width=True):
            with st.spinner("Computing statistics & generating narrative..."):
                try:
                    result = api.generate_report(st.session_state.session_id, stage_key, payload)
                    st.session_state[f"report_{stage_key}"] = result["markdown"]
                    st.session_state[f"stats_{stage_key}"] = result.get("stats", {})
                    if stage_key == "clustering":
                        st.session_state.cluster_ready = True
                        st.session_state.pop("clustered_df", None)
                except api.ApiError as e:
                    st.error(str(e))
    with col3:
        has_report = bool(st.session_state.get(f"report_{stage_key}"))
        if not has_report:
            st.download_button(
                "📄 Download PDF", data=b"", file_name=f"clustermaster_{stage_key}.pdf",
                mime="application/pdf", use_container_width=True, disabled=True,
            )
        else:
            # Only hit the backend to (re)build the PDF when we don't already
            # have bytes cached for this stage's *current* report — avoids
            # re-generating the whole PDF on every Streamlit rerun (which
            # happens on every widget interaction on the page, not just
            # clicks on this button).
            cache_key = f"pdf_bytes_{stage_key}"
            cache_report_key = f"pdf_bytes_{stage_key}_for_report"
            current_report = st.session_state[f"report_{stage_key}"]
            if st.session_state.get(cache_report_key) != current_report:
                st.session_state[cache_key] = _lazy_pdf(stage_key)
                st.session_state[cache_report_key] = current_report
            st.download_button(
                "📄 Download PDF",
                data=st.session_state.get(cache_key, b""),
                file_name=f"clustermaster_{stage_key}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.markdown("---")

    # ---- Data Layer (Computed Stats) ----
    stats = st.session_state.get(f"stats_{stage_key}")
    renderer = RENDERERS.get(stage_key)
    if stats and renderer:
        st.markdown("### 📊 The Data")
        with st.container():
            renderer(stats)

    # ---- Insight Layer (Agent Narrative) ----
    report_md = st.session_state.get(f"report_{stage_key}")
    if report_md:
        st.markdown("### 🤖 AI Analysis")
        st.markdown(
            f"""
            <div class="insight-card">
                {report_md}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if stats and not report_md:
            st.info("💡 The agent narrative will appear here after you click the generate button above.")

def _lazy_pdf(stage_key: str) -> bytes:
    if not st.session_state.get(f"report_{stage_key}"):
        return b""
    try:
        return api.download_pdf(st.session_state.session_id, stage_key)
    except api.ApiError:
        return b""

# ---------------------------------------------------------------------------
# 7. STAGE PAGES (CONDITIONAL ROUTING — UNCHANGED LOGIC, ENHANCED LAYOUT)
# ---------------------------------------------------------------------------
if active_stage == "data_health":
    stage_header("Data Health", "Checks for missing values, duplicates, constant columns, high-cardinality fields, and correlated features.")
    require_dataset()
    report_and_pdf_controls("data_health", "Generate Data Health Report")

elif active_stage == "eda":
    stage_header("Exploratory Analysis", "Summary statistics, correlations, variance structure, and unusual distributions.")
    require_dataset()
    if not st.session_state.get("report_data_health"):
        st.warning("⚠️ Run Data Health first — cleaning happens there and feeds this stage.")
    report_and_pdf_controls("eda", "Generate EDA Report")

elif active_stage == "clustering":
    stage_header("Clustering", "Choose an algorithm and parameters, then run clustering.")
    require_dataset()
    if not st.session_state.get("report_data_health"):
        st.warning("⚠️ Run Data Health first.")
    algo = st.selectbox("Algorithm", ["KMeans", "Gaussian Mixture (GMM)", "Agglomerative", "DBSCAN"])
    payload = {"algorithm": algo}
    if algo == "DBSCAN":
        payload["eps"] = st.slider("eps", 0.1, 5.0, 0.5)
        payload["min_samples"] = st.slider("min_samples", 2, 20, 5)
        payload["n_clusters"] = 5
    else:
        payload["n_clusters"] = st.slider("Number of clusters", 2, 10, 5)
        payload["eps"] = 0.5
        payload["min_samples"] = 5
    report_and_pdf_controls("clustering", "Run Clustering + Generate Report", payload)

elif active_stage == "cluster_profiles":
    stage_header("Cluster Profiles", "Persona-style summaries of each discovered cluster.")
    require_dataset()
    if not st.session_state.cluster_ready:
        st.info("Run clustering first on the **3. Clustering** tab.")
        st.stop()
    report_and_pdf_controls("cluster_profiles", "Generate Cluster Profiles")

elif active_stage == "cluster_comparison":
    stage_header("Cluster Comparison", "Compare two clusters side‑by‑side.")
    require_dataset()
    if not st.session_state.cluster_ready:
        st.info("Run clustering first on the **3. Clustering** tab.")
        st.stop()
    col1, col2 = st.columns(2)
    cluster_a = col1.number_input("Cluster A", min_value=0, value=0, step=1)
    cluster_b = col2.number_input("Cluster B", min_value=0, value=1, step=1)
    report_and_pdf_controls(
        "cluster_comparison", "Compare Clusters",
        {"cluster_a": int(cluster_a), "cluster_b": int(cluster_b)},
    )

elif active_stage == "anomaly_detection":
    stage_header("Anomaly Detection", "Isolation-Forest based detection of unusual records.")
    require_dataset()
    if not st.session_state.cluster_ready:
        st.info("Run clustering first on the **3. Clustering** tab.")
        st.stop()
    report_and_pdf_controls("anomaly_detection", "Detect Anomalies")

elif active_stage == "recommendations":
    stage_header("Business Recommendations", "Rule‑based actionable recommendations per cluster.")
    require_dataset()
    if not st.session_state.get("report_cluster_profiles"):
        st.info("Run Cluster Profiles first.")
        st.stop()
    report_and_pdf_controls("recommendations", "Generate Recommendations")

elif active_stage == "executive_dashboard":
    stage_header("Executive Dashboard", "At‑a‑glance KPIs from completed stages.")
    require_dataset()
    health = st.session_state.get("stats_data_health") or {}
    clustering = st.session_state.get("stats_clustering") or {}
    if health or clustering:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows analyzed", health.get("shape", {}).get("rows", "—"))
        c2.metric("Clusters found", clustering.get("n_clusters_found", "—"))
        sil = (clustering.get("evaluation_metrics") or {}).get("silhouette_score")
        c3.metric("Silhouette score", f"{sil:.3f}" if sil is not None else "n/a")
        c4.metric("Duplicate rows found", health.get("duplicate_rows", "—"))
        st.markdown("---")
    report_and_pdf_controls("executive_dashboard", "Generate Dashboard Callouts")

elif active_stage == "executive_report":
    stage_header("Executive Report", "Synthesizes every prior stage into one executive summary.")
    require_dataset()
    report_and_pdf_controls("executive_report", "Generate Executive Report")