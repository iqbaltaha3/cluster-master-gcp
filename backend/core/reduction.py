"""
core/reduction.py
Dimensionality reduction for visualization (PCA, t-SNE).
"""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


def reduce_pca(X: np.ndarray, n_components=2):
    pca = PCA(n_components=n_components, random_state=42)
    coords = pca.fit_transform(X)
    explained_variance = pca.explained_variance_ratio_.tolist()
    return coords, explained_variance


def reduce_tsne(X: np.ndarray, n_components=2, perplexity=30):
    n_samples = X.shape[0]
    perplexity = min(perplexity, max(5, n_samples // 4))
    tsne = TSNE(n_components=n_components, random_state=42, perplexity=perplexity, init="pca")
    coords = tsne.fit_transform(X)
    return coords
