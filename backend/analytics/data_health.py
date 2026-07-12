"""
analytics/data_health.py
Computes a data health report: missing values, duplicates, constant columns,
high-cardinality columns, correlated variables, outliers.
"""
import pandas as pd
import numpy as np


def compute_data_health(df: pd.DataFrame, high_cardinality_threshold=0.5, corr_threshold=0.9):
    n_rows, n_cols = df.shape
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    missing = df.isna().sum()
    missing_pct = (missing / max(n_rows, 1) * 100).round(2)
    missing_report = {
        col: {"missing_count": int(missing[col]), "missing_pct": float(missing_pct[col])}
        for col in df.columns if missing[col] > 0
    }

    duplicate_rows = int(df.duplicated().sum())

    constant_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]

    high_cardinality_cols = []
    for c in categorical_cols:
        ratio = df[c].nunique(dropna=True) / max(n_rows, 1)
        if ratio >= high_cardinality_threshold:
            high_cardinality_cols.append({"column": c, "unique_ratio": round(ratio, 2)})

    correlated_pairs = []
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().abs()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                val = corr.iloc[i, j]
                if val >= corr_threshold:
                    correlated_pairs.append({
                        "col_a": numeric_cols[i], "col_b": numeric_cols[j], "correlation": round(float(val), 3)
                    })

    outlier_counts = {}
    for c in numeric_cols:
        series = df[c].dropna()
        if len(series) < 4:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_outliers = int(((series < lower) | (series > upper)).sum())
        if n_outliers > 0:
            outlier_counts[c] = n_outliers

    suggestions = []
    if missing_report:
        suggestions.append("Impute or drop columns/rows with missing values before clustering.")
    if duplicate_rows > 0:
        suggestions.append(f"Remove {duplicate_rows} duplicate row(s).")
    if constant_cols:
        suggestions.append(f"Drop constant column(s): {', '.join(constant_cols)}.")
    if high_cardinality_cols:
        names = ", ".join(c["column"] for c in high_cardinality_cols)
        suggestions.append(f"Consider excluding or encoding high-cardinality column(s): {names}.")
    if correlated_pairs:
        suggestions.append("Highly correlated numeric features detected — consider removing redundancy.")
    if outlier_counts:
        suggestions.append("Outliers detected in some numeric columns — consider scaling method robust to outliers or investigate them.")

    return {
        "shape": {"rows": n_rows, "columns": n_cols},
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "missing_values": missing_report,
        "duplicate_rows": duplicate_rows,
        "constant_columns": constant_cols,
        "high_cardinality_columns": high_cardinality_cols,
        "highly_correlated_pairs": correlated_pairs,
        "outlier_counts": outlier_counts,
        "suggestions": suggestions,
    }
