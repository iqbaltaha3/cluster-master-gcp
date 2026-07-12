"""
tests/test_pipeline.py
Unit tests for the deterministic parts of the pipeline (statistics
computation, state transitions) using a fake Groq client so no network
call or API key is required. Run with: pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch

import pandas as pd
import pytest

from backend.state import ProjectState
from backend import pipeline


def fake_call_groq(system_prompt, user_prompt, max_tokens=900, temperature=0.4):
    return f"## Fake report\nThis is a fake agent response ({len(user_prompt)} chars of context)."


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "CustomerID": range(1, 51),
        "Gender": ["Male", "Female"] * 25,
        "Age": list(range(18, 68)),
        "AnnualIncome": [30000 + i * 1000 for i in range(50)],
        "SpendingScore": [i % 100 for i in range(50)],
    })


@pytest.fixture
def state(sample_df):
    s = ProjectState(session_id="test-session")
    s.df = sample_df
    s.dataset_name = "test.csv"
    return s


@patch("backend.agents.base.call_groq", side_effect=fake_call_groq)
def test_data_health_stage(mock_groq, state):
    md = pipeline.run_data_health(state)
    assert "Fake report" in md
    assert state.cleaned_df is not None
    assert "data_health" in state.reports
    assert "data_health" in state.project_memory


@patch("backend.agents.base.call_groq", side_effect=fake_call_groq)
def test_eda_requires_data_health_first(mock_groq, state):
    with pytest.raises(pipeline.StageError):
        pipeline.run_eda(state)


@patch("backend.agents.base.call_groq", side_effect=fake_call_groq)
def test_full_pipeline_happy_path(mock_groq, state):
    pipeline.run_data_health(state)
    pipeline.run_eda(state)
    pipeline.run_clustering(state, algorithm="KMeans", n_clusters=3)
    assert state.labels is not None
    assert state.clustering_info["algorithm"] == "KMeans"

    pipeline.run_cluster_profiles(state)
    pipeline.run_cluster_comparison(state, cluster_a=0, cluster_b=1)
    pipeline.run_anomaly_detection(state)
    pipeline.run_recommendations(state)
    pipeline.run_executive_dashboard(state)
    pipeline.run_executive_report(state)

    for stage in [
        "data_health", "eda", "clustering", "cluster_profiles",
        "cluster_comparison", "anomaly_detection", "recommendations",
        "executive_dashboard", "executive_report",
    ]:
        assert stage in state.reports
        assert stage in state.project_memory


@patch("backend.agents.base.call_groq", side_effect=fake_call_groq)
def test_project_memory_accumulates_context(mock_groq, state):
    pipeline.run_data_health(state)
    pipeline.run_eda(state)
    # by the time EDA runs, prior findings should include data_health's takeaway
    assert "data_health" in state.project_memory
    assert len(state.project_memory["data_health"]) > 0
