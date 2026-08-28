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
    quadrant that most needs new observations before HWO launch."""
    merged = stars[["hip_name", "hd_name", "sy_dist"]].merge(
        evidence[["hip_name", "evidence_completeness"]], on="hip_name", how="left"
    )
    merged["science_value_rank"] = merged["sy_dist"].rank(method="min").astype(int)
    merged["evidence_completeness_rank"] = (
        merged["evidence_completeness"].rank(method="min", ascending=False).astype(int)
    )
    return merged.sort_values("science_value_rank").reset_index(drop=True)
