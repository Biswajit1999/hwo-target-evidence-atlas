"""Target-ranking views.

Scientific value and evidence completeness are kept in two separate columns
and are never combined into a single score. Merging them would hide exactly
the information this project exists to surface: a scientifically excellent
target with poor evidence coverage looks identical to a mediocre,
well-characterized one under a single blended number. See
docs/METHODS.md for the rationale (this is a direct requirement of the
project's research question, not a stylistic choice).
"""
from __future__ import annotations

import pandas as pd


def rank_by_science_value(stars: pd.DataFrame) -> pd.DataFrame:
    """Rank by distance (closer = more favorable for direct imaging angular
    resolution and contrast, all else equal). This is a single transparent
    proxy, not a composite target-quality score -- see docs/LIMITATIONS.md
    for what it deliberately leaves out (spectral type, exozodi level,
    predicted planet-star contrast)."""
    return stars.sort_values("sy_dist").reset_index(drop=True)


def rank_by_evidence_completeness(evidence: pd.DataFrame) -> pd.DataFrame:
    return evidence.sort_values("evidence_completeness", ascending=True).reset_index(drop=True)


def combined_view(stars: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    """Both rankings side by side, still as two separate columns -- never a
    merged score. Useful for spotting the "high value, low evidence"
    quadrant that most needs new observations before HWO launch.

    Merges on ``target_id``, never ``hip_name``/``hip_number``: several
    targets are components of a wide binary sharing one Hipparcos number
    and hip_name string (e.g. HIP 72659 A/B), so a merge keyed on hip_name
    would match every A-row against every B-row sharing that name and
    silently fan out the result (164 stars -> 174 rows in an earlier
    version of this function; see
    tests/test_ranking.py::test_combined_view_does_not_fan_out_on_shared_hip_name).
    """
    merged = stars[["target_id", "hip_name", "hd_name", "sy_dist"]].merge(
        evidence[["target_id", "evidence_completeness"]], on="target_id", how="left"
    )
    assert len(merged) == len(stars), (
        f"combined_view merge changed row count: {len(stars)} -> {len(merged)}"
    )
    merged["distance_rank"] = merged["sy_dist"].rank(method="min").astype(int)
    merged["evidence_completeness_rank"] = (
        merged["evidence_completeness"].rank(method="min", ascending=False).astype(int)
    )
    return merged.sort_values("distance_rank").reset_index(drop=True)
