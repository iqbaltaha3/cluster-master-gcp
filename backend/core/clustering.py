"""
core/clustering.py
Wraps clustering algorithms behind a consistent interface.
"""
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture

ALGORITHMS = ["KMeans", "Gaussian Mixture (GMM)", "Agglomerative", "DBSCAN"]


def run_clustering(X: np.ndarray, algorithm: str, **params):
    """
    Run the selected clustering algorithm.
    Returns: labels (np.ndarray), model (fitted estimator), info (dict)
    """
    info = {"algorithm": algorithm, "params": params}

    if algorithm == "KMeans":
        n_clusters = params.get("n_clusters", 4)
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(X)

    elif algorithm == "Gaussian Mixture (GMM)":
        n_clusters = params.get("n_clusters", 4)
        model = GaussianMixture(n_components=n_clusters, random_state=42)
        labels = model.fit_predict(X)

    elif algorithm == "Agglomerative":
        n_clusters = params.get("n_clusters", 4)
        linkage = params.get("linkage", "ward")
        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        labels = model.fit_predict(X)

    elif algorithm == "DBSCAN":
        eps = params.get("eps", 0.5)
        min_samples = params.get("min_samples", 5)
        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(X)

    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    n_clusters_found = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1)) if -1 in labels else 0
    info["n_clusters_found"] = n_clusters_found
    info["n_noise_points"] = n_noise

    return labels, model, info


def suggest_kmeans_k_range(X: np.ndarray, k_min=2, k_max=10):
    """Compute inertia across a range of k values, for an elbow plot."""
    k_max = min(k_max, max(k_min + 1, X.shape[0] - 1))
    ks = list(range(k_min, k_max + 1))
    inertias = []
    for k in ks:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        model.fit(X)
        inertias.append(model.inertia_)
    return ks, inertias
