"""
analytics/cluster_comparison.py
Head-to-head comparison of two clusters.
"""
import pandas as pd
import numpy as np


def compare_clusters(df: pd.DataFrame, labels, cluster_a, cluster_b, numeric_cols, categorical_cols):
    data = df.copy()
    data["__cluster__"] = labels

    subset_a = data[data["__cluster__"] == cluster_a]
    subset_b = data[data["__cluster__"] == cluster_b]

    numeric_diffs = []
    for c in numeric_cols:
        mean_a, mean_b = subset_a[c].mean(), subset_b[c].mean()
        if pd.isna(mean_a) or pd.isna(mean_b):
            continue
        diff = mean_a - mean_b
        pct_diff = (diff / mean_b * 100) if mean_b != 0 else np.nan
        numeric_diffs.append({
            "column": c,
            "mean_a": round(float(mean_a), 3),
            "mean_b": round(float(mean_b), 3),
            "difference": round(float(diff), 3),
            "pct_difference": round(float(pct_diff), 2) if pd.notna(pct_diff) else None,
        })
    numeric_diffs.sort(key=lambda x: abs(x["difference"]), reverse=True)

    categorical_diffs = {}
    for c in categorical_cols:
        top_a = subset_a[c].value_counts(normalize=True).head(3).to_dict()
        top_b = subset_b[c].value_counts(normalize=True).head(3).to_dict()
        categorical_diffs[c] = {
            "cluster_a_top": {str(k): round(float(v) * 100, 1) for k, v in top_a.items()},
            "cluster_b_top": {str(k): round(float(v) * 100, 1) for k, v in top_b.items()},
        }

    return {
        "cluster_a": {"id": cluster_a, "size": len(subset_a)},
        "cluster_b": {"id": cluster_b, "size": len(subset_b)},
        "numeric_differences": numeric_diffs,
        "categorical_differences": categorical_diffs,
        "largest_differences": numeric_diffs[:5],
    }
