"""
core/evaluation.py
Cluster quality metrics.
"""
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score


def evaluate_clustering(X: np.ndarray, labels: np.ndarray):
    """
    Compute standard clustering quality metrics.
    Handles the case of noise points (-1) from DBSCAN and degenerate cases
    (fewer than 2 real clusters) gracefully.
    """
    mask = labels != -1
    unique_labels = set(labels[mask])

    metrics = {
        "silhouette_score": None,
        "davies_bouldin_score": None,
        "calinski_harabasz_score": None,
        "n_clusters": len(unique_labels),
    }

    if len(unique_labels) < 2 or mask.sum() < 3:
        return metrics

    X_eval = X[mask]
    labels_eval = labels[mask]

    try:
        metrics["silhouette_score"] = float(silhouette_score(X_eval, labels_eval))
    except Exception:
        pass
    try:
        metrics["davies_bouldin_score"] = float(davies_bouldin_score(X_eval, labels_eval))
    except Exception:
        pass
    try:
        metrics["calinski_harabasz_score"] = float(calinski_harabasz_score(X_eval, labels_eval))
    except Exception:
        pass

    return metrics


def interpret_silhouette(score):
    if score is None:
        return "Not available"
    if score >= 0.7:
        return "Strong, well-separated clusters"
    elif score >= 0.5:
        return "Reasonable cluster structure"
    elif score >= 0.25:
        return "Weak structure, some overlap"
    else:
        return "Little to no meaningful structure"
