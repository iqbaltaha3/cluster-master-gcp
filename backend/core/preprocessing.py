"""
core/preprocessing.py
Data cleaning and feature preparation utilities.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.impute import SimpleImputer


def get_column_types(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols


def clean_dataset(df: pd.DataFrame, drop_duplicates=True, drop_constant=True):
    """Basic cleaning: drop duplicate rows and constant columns."""
    cleaned = df.copy()
    report = {}

    if drop_duplicates:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        report["duplicates_removed"] = before - len(cleaned)

    if drop_constant:
        constant_cols = [c for c in cleaned.columns if cleaned[c].nunique(dropna=False) <= 1]
        cleaned = cleaned.drop(columns=constant_cols)
        report["constant_columns_removed"] = constant_cols

    return cleaned, report


def build_feature_matrix(
    df: pd.DataFrame,
    selected_columns,
    scaling_method="standard",
    impute_strategy="mean",
    encode_categoricals=True,
):
    """
    Build a numeric feature matrix ready for clustering.
    Returns: X (np.ndarray), feature_names (list), fitted preprocessing info (dict)
    """
    data = df[selected_columns].copy()
    numeric_cols, categorical_cols, _ = get_column_types(data)

    frames = []
    feature_names = []

    if numeric_cols:
        num_imputer = SimpleImputer(strategy=impute_strategy)
        num_data = num_imputer.fit_transform(data[numeric_cols])

        if scaling_method == "standard":
            scaler = StandardScaler()
        elif scaling_method == "minmax":
            scaler = MinMaxScaler()
        else:
            scaler = None

        if scaler is not None:
            num_data = scaler.fit_transform(num_data)

        frames.append(num_data)
        feature_names.extend(numeric_cols)

    if categorical_cols and encode_categoricals:
        cat_imputer = SimpleImputer(strategy="most_frequent")
        cat_filled = cat_imputer.fit_transform(data[categorical_cols])
        encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        cat_data = encoder.fit_transform(cat_filled)
        cat_names = encoder.get_feature_names_out(categorical_cols).tolist()
        frames.append(cat_data)
        feature_names.extend(cat_names)

    if not frames:
        raise ValueError("No usable columns selected for clustering.")

    X = np.hstack(frames)
    return X, feature_names, {
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols if encode_categoricals else [],
    }
