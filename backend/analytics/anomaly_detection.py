"""
analytics/anomaly_detection.py
Isolation Forest based anomaly detection.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(X: np.ndarray, df: pd.DataFrame, contamination=0.05, top_n=10):
    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(X)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(X)  # higher = more normal

    is_anomaly = preds == -1
    anomaly_score = -scores  # flip so higher = more anomalous

    result_df = df.copy()
    result_df["__is_anomaly__"] = is_anomaly
    result_df["__anomaly_score__"] = anomaly_score

    top_anomalies = result_df[result_df["__is_anomaly__"]].sort_values(
        "__anomaly_score__", ascending=False
    ).head(top_n)
    top_anomalies = top_anomalies.drop(columns=["__is_anomaly__"]).rename(
        columns={"__anomaly_score__": "anomaly_score"}
    )
    top_anomalies["anomaly_score"] = top_anomalies["anomaly_score"].round(4)

    return {
        "n_anomalies": int(is_anomaly.sum()),
        "pct_anomalies": round(float(is_anomaly.sum() / len(df) * 100), 2),
        "score_summary": {
            "min": round(float(anomaly_score.min()), 4),
            "mean": round(float(anomaly_score.mean()), 4),
            "max": round(float(anomaly_score.max()), 4),
        },
        # Plain records (not a DataFrame/ndarray) so this is directly usable
        # both by the LLM prompt and by the frontend table — no giant
        # per-row arrays get sent over the wire.
        "top_anomalies": top_anomalies.reset_index(drop=True).to_dict(orient="records"),
    }