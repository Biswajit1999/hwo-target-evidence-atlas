"""HGCA-vs-archive comparison between the two source catalogs.

This deliberately does NOT call the result a "conflict": ``sy_planets_flag
== "N"`` means "no archive-listed planet," not "confirmed single star with
no companion of any kind," so a significant HGCA acceleration alongside
``sy_planets_flag == "N"`` does not establish that the two catalogs
actually disagree -- the acceleration could be caused by a stellar,
brown-dwarf, or planetary-mass companion that simply isn't in the
archive's planet list. Every result row keeps both source values and their
provenance so a reader can judge for themselves; see docs/METHODS.md.
"""
from __future__ import annotations

import pandas as pd


def find_hgca_accelerators_without_archive_listed_planets(evidence: pd.DataFrame) -> pd.DataFrame:
    """Stars with a significant HGCA astrometric acceleration but no
    archive-listed planet in the NASA Exoplanet Archive Mission Star List.

    A significant acceleration (see evidence.ACCEL_SIGNIFICANCE_ALPHA, and
    ``hgca_significant_accel_fdr`` for the multiple-testing-corrected
    version) means the star's proper motion is not consistent with a
    single, stationary point mass -- i.e. there is very likely an
    unresolved companion (stellar, brown-dwarf, or planetary-mass).
    ``sy_planets_flag == "N"`` means no archive-listed planet, NOT a
    confirmed single-star / no-companion determination -- the two catalogs
    are not necessarily in disagreement, since the companion causing the
    acceleration may simply not be a planet, or not yet be catalogued as
    one. Companion nature (mass, period, or even stellar-vs-planetary) is
    undetermined from this comparison alone; this identifies candidates for
    follow-up, not confirmed conflicts.
    """
    mask = (
        evidence["hgca_significant_accel"].fillna(False)
        & (evidence["sy_planets_flag"] == "N")
    )
    cols = ["target_id", "hip_name", "hd_name", "sy_planets_flag", "hgca_chi2",
            "hgca_accel_pvalue", "hgca_accel_qvalue", "hgca_significant_accel_fdr"]
    return evidence.loc[mask, cols].sort_values("hgca_accel_pvalue")


def find_missing_evidence(evidence: pd.DataFrame, category: str) -> pd.DataFrame:
    """Stars with no evidence at all for a given category (schema-checked
    against evidence.EVIDENCE_CATEGORIES by the caller / CLI)."""
    mask = ~evidence[category].astype(bool)
    return evidence.loc[mask, ["hip_name", "hd_name", category]]
