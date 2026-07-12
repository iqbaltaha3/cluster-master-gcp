"""
frontend/app.py
ClusterMaster — Streamlit frontend.
REDESIGN v5.3 — Soft Baby Blue & Baby Pink Theme.
Gentle, modern, and professional.
"""
import io

import pandas as pd
import streamlit as st

import api_client as api

# ---------------------------------------------------------------------------
# 1. GLOBAL DESIGN SYSTEM — Baby Blue & Baby Pink
# ---------------------------------------------------------------------------
st.set_page_config(page_title="ClusterMaster", page_icon="🧭", layout="wide")

DESIGN_CSS = """
<style>
:root {
  --color-primary: #60A5FA;           /* Baby Blue */
  --color-primary-hover: #3B82F6;
  --color-primary-light: #E0F2FE;
  --color-accent: #F9A8D4;            /* Baby Pink */
  --color-accent-hover: #F472B6;
  --color-success: #4ADE80;
  --color-bg: #F8FAFC;
  --color-surface: #FFFFFF;
  --color-border: #E0E7FF;
  --color-text-primary: #1E2937;
  --color-text-secondary: #475569;
  --color-text-muted: #94A3B8;
  --font-family: 'Inter', system-ui, sans-serif;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 2px 6px rgba(0,0,0,0.04);
  --shadow-md: 0 6px 16px rgba(0,0,0,0.06);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.08);
}

html, body, .stApp {
  font-family: var(--font-family);
  background-color: var(--color-bg) !important;
  color: var(--color-text-primary);
}

.main .block-container {
  padding: 2.5rem 2.5rem 3rem !important;
  max-width: 1280px !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--color-surface) !important;
  border-right: 1px solid var(--color-border) !important;
  box-shadow: 3px 0 15px rgba(0,0,0,0.04);
}

/* Navigation */
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding: 12px 16px !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {
  background: var(--color-primary) !important;
  color: white !important;
}

/* Metrics */
div[data-testid="stMetric"] {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem !important;
  box-shadow: var(--shadow-sm);
}
div[data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

/* Buttons */
.stButton > button[kind="primary"] {
  background: var(--color-primary) !important;
  color: white !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--color-primary-hover) !important;
}

/* Download - Baby Pink */
.stDownloadButton > button {
  background: var(--color-accent) !important;
  color: #1E2937 !important;
}

/* Insight Card */
.insight-card {
  background: var(--color-surface);
  border-left: 5px solid var(--color-accent);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  padding: 1.75rem 2rem;
  box-shadow: var(--shadow-sm);
  margin: 1.5rem 0;
}

/* Guidance */
.guidance {
  background: var(--color-primary-light);
  border-left: 4px solid var(--color-primary);
  padding: 1rem 1.5rem;
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}

/* Progress */
.custom-progress {
  height: 6px;
  background: var(--color-border);
  border-radius: 9999px;
  overflow: hidden;
}
.custom-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
  border-radius: 9999px;
}
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. CONFIG & SESSION STATE
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
# 3. SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-size: 32px;">🧭</span>
            <span style="font-size: 24px; font-weight: 800; letter-spacing: -0.02em;">ClusterMaster</span>
        </div>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">
            Customer segmentation platform
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### Data Upload")
    st.caption("CSV, Excel, JSON, Parquet")
    upload = st.file_uploader("Upload dataset", type=["csv", "tsv", "xlsx", "xls", "json", "parquet"], label_visibility="collapsed")

    if upload is not None and st.session_state.get("last_upload_name") != upload.name:
        with st.spinner("Processing dataset..."):
            try:
                result = api.upload_dataset(st.session_state.session_id, upload)
                st.session_state.dataset_loaded = True
                st.session_state.last_upload_name = upload.name
                st.session_state.domain_brief = result.get("domain_brief", "")
                st.session_state.dataset_info = result
                reset_after_upload()
            except api.ApiError as e:
                st.error(f"Upload failed: {e}")

    if st.session_state.dataset_loaded:
        info = st.session_state.dataset_info
        st.success(f"Loaded: {info.get('dataset_name', 'Dataset')} ({info.get('n_rows', 0)} rows)")

    st.markdown("---")

    current_idx = STAGES.index(next((s for s in STAGES if s[0] == st.session_state.get("active_stage", "data_health")), STAGES[0]))
    total = len(STAGES)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; color: var(--color-text-secondary);">
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
    choice = st.radio("Navigate", labels, index=current_idx, label_visibility="collapsed", key="stage_radio")
    active_stage = STAGES[labels.index(choice)][0]
    st.session_state["active_stage"] = active_stage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def require_dataset():
    if not st.session_state.dataset_loaded:
        st.info("Please upload a dataset in the sidebar to begin.")
        st.stop()

def stage_header(title: str, description: str = ""):
    st.markdown(f"<h1 style='font-size: 28px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 8px;'>{title}</h1>", unsafe_allow_html=True)
    if description:
        st.markdown(f"<p style='color: var(--color-text-secondary); font-size: 1.05rem;'>{description}</p>", unsafe_allow_html=True)

def _get_clustered_df():
    if "clustered_df" not in st.session_state:
        try:
            csv_bytes = api.download_clustered_csv(st.session_state.session_id)
            st.session_state.clustered_df = pd.read_csv(io.BytesIO(csv_bytes))
        except:
            return None
    return st.session_state.clustered_df

# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------
def render_data_health(stats: dict):
    if not stats: return
    shape = stats.get("shape", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", shape.get("rows", "—"))
    c2.metric("Columns", shape.get("columns", "—"))
    c3.metric("Duplicates", stats.get("duplicate_rows", 0))
    c4.metric("Missing Columns", len(stats.get("missing_values", {})))

def render_eda(stats: dict):
    if not stats: return
    if stats.get("summary_statistics"):
        st.dataframe(pd.DataFrame.from_dict(stats["summary_statistics"], orient="index"), use_container_width=True)

def render_clustering(stats: dict):
    if not stats: return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clusters", stats.get("n_clusters_found", "—"))
    c2.metric("Noise", stats.get("n_noise_points", 0))

def render_cluster_profiles(stats: dict):
    if not stats: return
    for cid, profile in stats.items():
        with st.expander(f"Cluster {cid} — {profile.get('size', 0)} records"):
            st.write(profile.get("numeric_profile", {}))

def render_cluster_comparison(stats: dict):
    if not stats: return
    st.write("Comparison data loaded.")

def render_anomaly_detection(stats: dict):
    if not stats: return
    st.metric("Anomalies Found", stats.get("n_anomalies", 0))

def render_recommendations(stats):
    if not stats: return
    st.dataframe(pd.DataFrame(stats), use_container_width=True)

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
# Controls
# ---------------------------------------------------------------------------
def report_and_pdf_controls(stage_key: str, generate_label: str, payload: dict = None):
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        if st.session_state.get(f"report_{stage_key}"):
            st.success("✅ Analysis complete")
        else:
            st.info("⏳ Awaiting generation")
    with col2:
        if st.button(generate_label, type="primary", use_container_width=True):
            with st.spinner("Generating insights..."):
                try:
                    result = api.generate_report(st.session_state.session_id, stage_key, payload)
                    st.session_state[f"report_{stage_key}"] = result["markdown"]
                    st.session_state[f"stats_{stage_key}"] = result.get("stats", {})
                    if stage_key == "clustering":
                        st.session_state.cluster_ready = True
                except api.ApiError as e:
                    st.error(str(e))
    with col3:
        has_report = bool(st.session_state.get(f"report_{stage_key}"))
        st.download_button("Download PDF", data=b"", file_name=f"clustermaster_{stage_key}.pdf", disabled=not has_report, use_container_width=True)

    st.markdown("---")

    stats = st.session_state.get(f"stats_{stage_key}")
    if stats and RENDERERS.get(stage_key):
        st.markdown("### Data Summary")
        RENDERERS[stage_key](stats)

    report_md = st.session_state.get(f"report_{stage_key}")
    if report_md:
        st.markdown("### AI Insights")
        st.markdown(f'<div class="insight-card">{report_md}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# STAGE PAGES
# ---------------------------------------------------------------------------
if active_stage == "data_health":
    stage_header("Data Health", "Assess data quality, identify issues, and prepare your dataset.")
    require_dataset()
    st.markdown('<div class="guidance"><strong>How to use:</strong> Upload your dataset in the sidebar, then click "Generate Data Health Report" to run automated checks.</div>', unsafe_allow_html=True)
    report_and_pdf_controls("data_health", "Generate Data Health Report")

elif active_stage == "eda":
    stage_header("Exploratory Analysis", "Discover patterns, correlations, and statistical insights.")
    require_dataset()
    st.markdown('<div class="guidance"><strong>How to use:</strong> Click "Generate EDA Report" after completing Data Health.</div>', unsafe_allow_html=True)
    report_and_pdf_controls("eda", "Generate EDA Report")

elif active_stage == "clustering":
    stage_header("Clustering", "Segment your customers using machine learning.")
    require_dataset()
    algo = st.selectbox("Algorithm", ["KMeans", "Gaussian Mixture", "DBSCAN"])
    payload = {"algorithm": algo}
    if algo != "DBSCAN":
        payload["n_clusters"] = st.slider("Number of Clusters", 2, 10, 4)
    st.markdown('<div class="guidance"><strong>How to use:</strong> Choose algorithm and parameters, then click "Run Clustering".</div>', unsafe_allow_html=True)
    report_and_pdf_controls("clustering", "Run Clustering + Generate Report", payload)

elif active_stage == "cluster_profiles":
    stage_header("Cluster Profiles", "Detailed view of each customer segment.")
    require_dataset()
    if not st.session_state.get("cluster_ready"):
        st.info("Run Clustering first.")
        st.stop()
    report_and_pdf_controls("cluster_profiles", "Generate Cluster Profiles")

elif active_stage == "cluster_comparison":
    stage_header("Cluster Comparison", "Compare two clusters side by side.")
    require_dataset()
    if not st.session_state.get("cluster_ready"):
        st.info("Run Clustering first.")
        st.stop()
    col1, col2 = st.columns(2)
    a = col1.number_input("Cluster A", 0, 20, 0)
    b = col2.number_input("Cluster B", 0, 20, 1)
    report_and_pdf_controls("cluster_comparison", "Compare Clusters", {"cluster_a": int(a), "cluster_b": int(b)})

elif active_stage == "anomaly_detection":
    stage_header("Anomaly Detection", "Identify unusual records.")
    require_dataset()
    if not st.session_state.get("cluster_ready"):
        st.info("Run Clustering first.")
        st.stop()
    report_and_pdf_controls("anomaly_detection", "Detect Anomalies")

elif active_stage == "recommendations":
    stage_header("Business Recommendations", "Actionable insights per cluster.")
    require_dataset()
    report_and_pdf_controls("recommendations", "Generate Recommendations")

elif active_stage == "executive_dashboard":
    stage_header("Executive Dashboard", "High-level summary and KPIs.")
    require_dataset()
    report_and_pdf_controls("executive_dashboard", "Generate Dashboard")

elif active_stage == "executive_report":
    stage_header("Executive Report", "Full synthesized report.")
    require_dataset()
    report_and_pdf_controls("executive_report", "Generate Executive Report")

else:
    st.info("Select a stage from the sidebar.")