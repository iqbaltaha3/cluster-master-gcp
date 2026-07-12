"""
analytics/cluster_profiler.py
Builds per-cluster profiles: size, averages, medians, dominant categories,
and deviation from overall dataset averages.
"""
import pandas as pd
import numpy as np


def profile_clusters(df: pd.DataFrame, labels, numeric_cols, categorical_cols):
    data = df.copy()
    data["__cluster__"] = labels

    overall_numeric_mean = data[numeric_cols].mean() if numeric_cols else pd.Series(dtype=float)
    profiles = {}

    for cluster_id in sorted(data["__cluster__"].unique()):
        subset = data[data["__cluster__"] == cluster_id]
        size = len(subset)

        numeric_profile = {}
        for c in numeric_cols:
            mean_val = subset[c].mean()
            median_val = subset[c].median()
            overall_mean = overall_numeric_mean[c]
            deviation_pct = (
                (mean_val - overall_mean) / overall_mean * 100
                if pd.notna(overall_mean) and overall_mean != 0
                else np.nan
            )
            numeric_profile[c] = {
                "mean": round(float(mean_val), 3) if pd.notna(mean_val) else None,
                "median": round(float(median_val), 3) if pd.notna(median_val) else None,
                "deviation_from_overall_pct": round(float(deviation_pct), 2) if pd.notna(deviation_pct) else None,
            }

        categorical_profile = {}
        for c in categorical_cols:
            if subset[c].dropna().empty:
                continue
            top = subset[c].value_counts(normalize=True).head(3)
            categorical_profile[c] = [
                {"value": str(idx), "share_pct": round(float(val) * 100, 1)} for idx, val in top.items()
            ]

        # Distinguishing features: numeric columns with largest absolute deviation
        distinguishing = sorted(
            [(c, numeric_profile[c]["deviation_from_overall_pct"]) for c in numeric_cols
             if numeric_profile[c]["deviation_from_overall_pct"] is not None],
            key=lambda x: abs(x[1]), reverse=True
        )[:5]

        profiles[str(cluster_id)] = {
            "cluster_id": int(cluster_id) if cluster_id != -1 else "noise",
            "size": size,
            "size_pct": round(size / len(data) * 100, 1),
            "numeric_profile": numeric_profile,
            "categorical_profile": categorical_profile,
            "distinguishing_features": [{"column": c, "deviation_pct": d} for c, d in distinguishing],
        }

    return profiles


def build_radar_data(profiles: dict, numeric_cols, top_k_features=6):
    """Prepare normalized data for a radar chart comparing clusters on shared numeric features."""
    if not numeric_cols:
        return [], {}
    features = numeric_cols[:top_k_features]
    raw = {}
    for cid, p in profiles.items():
        raw[cid] = [p["numeric_profile"].get(f, {}).get("mean", 0) or 0 for f in features]

    # Normalize each feature (column-wise) to 0-1 for comparable radar shape
    arr = np.array(list(raw.values()), dtype=float)
    mins = arr.min(axis=0)
    maxs = arr.max(axis=0)
    ranges = np.where((maxs - mins) == 0, 1, maxs - mins)
    normalized = (arr - mins) / ranges

    normalized_dict = {cid: normalized[i].tolist() for i, cid in enumerate(raw.keys())}
    return features, normalized_dict
