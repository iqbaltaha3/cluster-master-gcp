"""
analytics/eda.py
Exploratory data analysis computations.
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def compute_summary_statistics(df: pd.DataFrame, numeric_cols):
    if not numeric_cols:
        return {}
    desc = df[numeric_cols].describe().T
    desc["skewness"] = df[numeric_cols].skew()
    desc["kurtosis"] = df[numeric_cols].kurt()
    return desc.round(3).to_dict(orient="index")


def compute_pca_variance(df: pd.DataFrame, numeric_cols, max_components=10):
    if len(numeric_cols) < 2:
        return None
    X = df[numeric_cols].dropna()
    if len(X) < 3:
        return None
    X_scaled = StandardScaler().fit_transform(X)
    n_components = min(max_components, X_scaled.shape[1], X_scaled.shape[0])
    pca = PCA(n_components=n_components, random_state=42)
    pca.fit(X_scaled)
    return {
        "explained_variance_ratio": pca.explained_variance_ratio_.round(4).tolist(),
        "cumulative_variance": np.cumsum(pca.explained_variance_ratio_).round(4).tolist(),
    }


def top_correlations(df: pd.DataFrame, numeric_cols, top_n=5):
    if len(numeric_cols) < 2:
        return []
    corr = df[numeric_cols].corr()
    pairs = []
    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            pairs.append((numeric_cols[i], numeric_cols[j], corr.iloc[i, j]))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    return [{"col_a": a, "col_b": b, "correlation": round(float(c), 3)} for a, b, c in pairs[:top_n]]


def unusual_distributions(df: pd.DataFrame, numeric_cols, skew_threshold=1.0):
    flagged = []
    for c in numeric_cols:
        skew = df[c].skew()
        if pd.notna(skew) and abs(skew) >= skew_threshold:
            flagged.append({"column": c, "skewness": round(float(skew), 3),
                             "direction": "right-skewed" if skew > 0 else "left-skewed"})
    return flagged
