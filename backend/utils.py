"""
backend/utils.py
JSON-safety helpers.

Analytics functions in backend/analytics and backend/core are written for
convenience: they freely return numpy scalars, numpy arrays, and pandas
Series/DataFrames. That's fine as long as the only consumer is the LLM
(which just gets str()'d text). But now that we also want to hand the raw
`state.stats[stage_key]` dict to the frontend as real JSON (so it can
render actual tables/metrics/charts instead of only LLM prose), it has to
be converted into plain Python types first — Pydantic/FastAPI cannot
serialize numpy/pandas objects on its own, and will throw 500s.

to_jsonable() walks any nested combination of dict/list/numpy/pandas
values and returns something json.dumps-safe.
"""
import re

import numpy as np
import pandas as pd


def safe_download_filename(name: str, fallback: str = "clustermaster") -> str:
    """Sanitize a user-controlled string (e.g. an uploaded filename) before
    it's embedded in a Content-Disposition header. Strips anything that
    isn't alphanumeric/dot/dash/underscore, collapses whitespace, and
    guards against empty results and header-injection characters (CR/LF/")
    that could otherwise corrupt the response headers or downstream
    filename parsing."""
    if not name:
        return fallback
    # drop CR/LF/quotes outright, then whitelist a safe character set
    name = name.replace("\r", "").replace("\n", "").replace('"', "")
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    name = name.strip("._-")
    return name or fallback


def to_jsonable(obj):
    if obj is None:
        return None
    if isinstance(obj, bool) or isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        return None if f != f else f  # NaN != NaN
    if isinstance(obj, str):
        return obj
    if isinstance(obj, np.ndarray):
        return [to_jsonable(v) for v in obj.tolist()]
    if isinstance(obj, pd.Series):
        return [to_jsonable(v) for v in obj.tolist()]
    if isinstance(obj, pd.DataFrame):
        return [to_jsonable(row) for row in obj.to_dict(orient="records")]
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    # Fallback for anything else (e.g. numpy datatypes we didn't anticipate)
    return str(obj)