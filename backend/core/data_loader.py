"""
core/data_loader.py
Handles loading of user-uploaded datasets into pandas DataFrames.
"""
import pandas as pd
import io


SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".tsv", ".json", ".parquet"]


def load_dataset(uploaded_file, filename: str = None) -> pd.DataFrame:
    """
    Load a dataset from a file-like object into a DataFrame.
    Supports csv, tsv, xlsx, xls, json, parquet.

    `filename` is required when `uploaded_file` doesn't expose a `.name`
    attribute (e.g. a raw BytesIO from a FastAPI UploadFile).
    """
    name = (filename or getattr(uploaded_file, "name", None) or "").lower()
    if not name:
        raise ValueError("Could not determine filename; pass filename= explicitly.")

    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".tsv"):
        df = pd.read_csv(uploaded_file, sep="\t")
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    elif name.endswith(".parquet"):
        df = pd.read_parquet(uploaded_file)
    else:
        raise ValueError(
            f"Unsupported file type for '{name}'. "
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Normalize column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_sample_dataset(name: str = "mall_customers") -> pd.DataFrame:
    """
    Generate a small synthetic sample dataset so users can try the app
    without uploading their own data.
    """
    import numpy as np
    rng = np.random.default_rng(42)
    n = 400

    segments = []
    for _ in range(n):
        seg = rng.choice(["young_spender", "budget_family", "premium_loyal", "occasional"], p=[0.3, 0.3, 0.2, 0.2])
        if seg == "young_spender":
            age = rng.normal(27, 4)
            income = rng.normal(45000, 8000)
            spending = rng.normal(78, 10)
        elif seg == "budget_family":
            age = rng.normal(40, 6)
            income = rng.normal(52000, 9000)
            spending = rng.normal(35, 10)
        elif seg == "premium_loyal":
            age = rng.normal(45, 8)
            income = rng.normal(110000, 15000)
            spending = rng.normal(82, 8)
        else:
            age = rng.normal(33, 10)
            income = rng.normal(60000, 20000)
            spending = rng.normal(45, 15)
        segments.append((age, income, spending))

    ages, incomes, spendings = zip(*segments)
    genders = rng.choice(["Male", "Female"], size=n)
    df = pd.DataFrame({
        "CustomerID": range(1, n + 1),
        "Gender": genders,
        "Age": [max(18, round(a)) for a in ages],
        "AnnualIncome": [max(10000, round(i)) for i in incomes],
        "SpendingScore": [min(100, max(1, round(s))) for s in spendings],
    })
    return df
