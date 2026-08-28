"""Per-star, per-category evidence-completeness matrix.

Six evidence categories are scored for each of the 164
``DI_STARS_EXEP`` targets. Each category records whether a *measurement
exists at all* (evidence present) -- not whether the star is favorable. A
"no known companion" flag and "no measurement attempted" are different
things and are never conflated here; see the ``EVIDENCE_CATEGORIES``
docstring for exactly what "present" means for each category, and
docs/METHODS.md for the rationale.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import chi2 as chi2_dist

# HGCA acceleration significance: chi2 with 2 degrees of freedom (Brandt
# 2021). p < ACCEL_SIGNIFICANCE_ALPHA is reported as a "significant"
# acceleration; the raw p-value is also always reported so a reader can
# apply a different threshold.
ACCEL_SIGNIFICANCE_ALPHA = 0.01


@dataclass(frozen=True)
class EvidenceCategory:
    key: str
    description: str
    present_fn: callable  # row (pd.Series) -> bool | None (None = not applicable)


def _stellar_parameters_present(row: pd.Series) -> bool:
    fields = ["st_teff", "st_mass", "st_rad", "st_logg"]
    return all(pd.notna(row.get(f)) for f in fields)


def _activity_present(row: pd.Series) -> bool:
    return pd.notna(row.get("st_log_rhk"))


def _multiplicity_present(row: pd.Series) -> bool:
    # Evidence "present" here means the star has a Washington Double Star
    # catalog cross-match record -- i.e. a multiplicity assessment exists.
    # Absence (wds_designation is null) means "no WDS entry found", which
    # is NOT equivalent to "confirmed single star" -- see docs/METHODS.md.
    return pd.notna(row.get("wds_designation"))


def _rv_companion_present(row: pd.Series) -> bool:
    # sy_planets_flag is always populated ("Y"/"N") in DI_STARS_EXEP for
    # this target list, so "evidence present" is true for every row; the
    # informative quantity is the *value*, tracked separately in
    # conflicts.py. This category is kept for schema completeness and to
    # make an actual missing-value future case visible if the upstream
    # table ever changes.
    return pd.notna(row.get("sy_planets_flag"))


def _exozodi_present(row: pd.Series) -> bool:
    return pd.notna(row.get("sy_disks_flag"))


def _astrometric_accel_present(row: pd.Series) -> bool:
    return pd.notna(row.get("hgca_chi2"))


EVIDENCE_CATEGORIES = [
    EvidenceCategory(
        "stellar_parameters",
        "Teff, mass, radius, and logg all measured (NASA Exoplanet Archive)",
        _stellar_parameters_present,
    ),
    EvidenceCategory(
        "activity",
        "Chromospheric activity index log(R'HK) measured",
        _activity_present,
    ),
    EvidenceCategory(
        "multiplicity",
        "Washington Double Star catalog cross-match exists (presence of a "
        "record, not a Y/N single-star determination)",
        _multiplicity_present,
    ),
    EvidenceCategory(
        "known_companions",
        "Known-planet flag assessed (sy_planets_flag populated)",
        _rv_companion_present,
    ),
    EvidenceCategory(
        "exozodiacal_dust",
        "Circumstellar-disk flag assessed (sy_disks_flag populated)",
        _exozodi_present,
    ),
    EvidenceCategory(
        "astrometric_acceleration",
        "Star has a Hipparcos-Gaia Catalog of Accelerations (HGCA) entry",
        _astrometric_accel_present,
    ),
]


def build_evidence_matrix(stars: pd.DataFrame, hgca: pd.DataFrame) -> pd.DataFrame:
    """Join the star table with the HGCA cross-match and score every
    evidence category for every star.

    Returns one row per star with a boolean column per category plus
    ``evidence_completeness`` (fraction of categories present) and, where
    available, ``hgca_chi2`` / ``hgca_accel_pvalue`` / ``hgca_significant_accel``.
    """
    hgca = hgca.rename(columns={"HIP": "hip_number", "chi2": "hgca_chi2"})
    # Defensive dedupe: several DI_STARS_EXEP targets are components of a
    # wide binary sharing one Hipparcos number (e.g. Xi Boo A/B both under
    # HIP 72659). Without this, a duplicated hgca row for that HIP would
    # fan out the merge below (each of the two star rows would match both
    # hgca rows), silently inflating the output row count.
    hgca_unique = hgca.drop_duplicates(subset="hip_number", keep="first")
    merged = stars.merge(
        hgca_unique[["hip_number", "hgca_chi2"]], on="hip_number", how="left"
    )
    assert len(merged) == len(stars), (
        f"evidence matrix merge changed row count: {len(stars)} -> {len(merged)}"
    )

    merged["hgca_accel_pvalue"] = merged["hgca_chi2"].apply(
        lambda c: float(chi2_dist.sf(c, df=2)) if pd.notna(c) else np.nan
    )
    merged["hgca_significant_accel"] = merged["hgca_accel_pvalue"] < ACCEL_SIGNIFICANCE_ALPHA

    for cat in EVIDENCE_CATEGORIES:
        merged[cat.key] = merged.apply(cat.present_fn, axis=1)

    cat_cols = [c.key for c in EVIDENCE_CATEGORIES]
    merged["evidence_completeness"] = merged[cat_cols].mean(axis=1)

    id_cols = ["hip_name", "hd_name", "hip_number", "sy_dist", "sy_planets_flag", "sy_disks_flag"]
    return merged[id_cols + cat_cols + ["evidence_completeness", "hgca_chi2",
                                         "hgca_accel_pvalue", "hgca_significant_accel"]]
