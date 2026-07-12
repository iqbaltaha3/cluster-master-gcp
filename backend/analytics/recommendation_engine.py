"""
analytics/recommendation_engine.py
Deterministic, rule-based business recommendation engine.
The output of these rules is later phrased into prose by the LLM layer.
"""
import numpy as np


def generate_recommendations(profiles: dict, target_column_hint=None):
    """
    profiles: dict produced by analytics.cluster_profiler.profile_clusters
    target_column_hint: optional column name representing an "engagement" or
        "value" style metric (e.g. SpendingScore, Revenue) to prioritize rules on.
    Returns a list of rule-based recommendation dicts.
    """
    recs = []
    sizes = {cid: p["size"] for cid, p in profiles.items()}
    if not sizes:
        return recs
    avg_size = np.mean(list(sizes.values()))
    max_size = max(sizes.values())

    # Try to auto-detect a "value"-like numeric column if hint not given
    candidate_cols = set()
    for p in profiles.values():
        candidate_cols.update(p["numeric_profile"].keys())

    value_col = target_column_hint
    if value_col is None:
        for keyword in ["spend", "revenue", "income", "value", "score", "purchase"]:
            matches = [c for c in candidate_cols if keyword.lower() in c.lower()]
            if matches:
                value_col = matches[0]
                break

    for cid, p in profiles.items():
        size = p["size"]
        size_pct = p["size_pct"]
        is_largest = size == max_size

        value_mean = None
        value_deviation = None
        if value_col and value_col in p["numeric_profile"]:
            value_mean = p["numeric_profile"][value_col]["mean"]
            value_deviation = p["numeric_profile"][value_col]["deviation_from_overall_pct"]

        # Rule 1: Largest cluster with low value/engagement -> growth opportunity
        if is_largest and value_deviation is not None and value_deviation < -15:
            recs.append({
                "cluster_id": cid,
                "type": "Growth Opportunity",
                "reasoning": f"Largest segment ({size_pct}% of customers) with {value_col} "
                             f"{abs(value_deviation):.1f}% below average.",
            })

        # Rule 2: Small cluster with high value -> VIP retention
        if size_pct <= 15 and value_deviation is not None and value_deviation > 20:
            recs.append({
                "cluster_id": cid,
                "type": "VIP Retention",
                "reasoning": f"Small but high-value segment ({size_pct}% of customers) with {value_col} "
                             f"{value_deviation:.1f}% above average.",
            })

        # Rule 3: High internal variance -> consider further segmentation
        high_variance_features = [
            f["column"] for f in p["distinguishing_features"] if abs(f["deviation_pct"] or 0) > 40
        ]
        if len(high_variance_features) >= 3:
            recs.append({
                "cluster_id": cid,
                "type": "Further Segmentation Candidate",
                "reasoning": f"Segment shows large internal spread across multiple features "
                             f"({', '.join(high_variance_features[:3])}), suggesting it may contain "
                             f"sub-segments worth separating.",
            })

        # Rule 4: Mid-size average-value cluster -> standard nurture
        if not recs or all(r["cluster_id"] != cid for r in recs):
            recs.append({
                "cluster_id": cid,
                "type": "Standard Nurture",
                "reasoning": f"Segment ({size_pct}% of customers) does not show extreme value or size "
                             f"characteristics; maintain standard engagement.",
            })

    return recs
