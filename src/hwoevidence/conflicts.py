"""Conflict detection between the two source catalogs.

A "conflict" here means two independent measurements are in tension, not
that either is wrong -- see docs/METHODS.md. Every conflict row keeps both
source values and their provenance so a reader can judge for themselves.
"""
from __future__ import annotations

import pandas as pd


def find_undisclosed_companion_conflicts(evidence: pd.DataFrame) -> pd.DataFrame:
    """Stars with a significant HGCA astrometric acceleration but no known
    companion flagged in the NASA Exoplanet Archive Mission Star List.

    A significant acceleration (see evidence.ACCEL_SIGNIFICANCE_ALPHA) means
    the star's proper motion is not consistent with a single, stationary
    point mass -- i.e. there is very likely an unresolved companion
    (stellar, brown-dwarf, or planetary-mass). If ``sy_planets_flag`` is "N"
    at the same time, the two catalogs disagree about whether this system is
    single, which matters directly for HWO target vetting (an unrecognized
    companion can contaminate or preclude a direct-imaging observation).
    This is a *candidate* conflict for follow-up, not a confirmed
    companion -- the acceleration alone does not establish mass or period.
    """
    mask = (
        evidence["hgca_significant_accel"].fillna(False)
        & (evidence["sy_planets_flag"] == "N")
    )
    cols = ["hip_name", "hd_name", "sy_planets_flag", "hgca_chi2", "hgca_accel_pvalue"]
    return evidence.loc[mask, cols].sort_values("hgca_accel_pvalue")


def find_missing_evidence(evidence: pd.DataFrame, category: str) -> pd.DataFrame:
    """Stars with no evidence at all for a given category (schema-checked
    against evidence.EVIDENCE_CATEGORIES by the caller / CLI)."""
    mask = ~evidence[category].astype(bool)
    return evidence.loc[mask, ["hip_name", "hd_name", category]]
