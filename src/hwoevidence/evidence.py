"""Per-star, per-category evidence-completeness matrix.

Six categories are scored for each of the 164 ``DI_STARS_EXEP`` targets
(``EVIDENCE_CATEGORIES``), but only four of them -- the ones that record
whether a real, non-universal measurement exists -- feed into
``evidence_completeness`` (``COVERAGE_CATEGORIES``). Two categories
(``archive_planet_flag_populated``, ``archive_disk_flag_populated``) are
tracked but deliberately excluded: they are true for essentially every row
in this target list regardless of whether any actual companion or exozodi
observation was ever made, so including them in a completeness average
would silently inflate every star's score by a fixed, uninformative
amount. A "no known companion" flag and "no measurement attempted" are
different things and are never conflated here; see the
``EVIDENCE_CATEGORIES`` docstrings for exactly what "present" means for
each category, and docs/METHODS.md / docs/LIMITATIONS.md for the
rationale.
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
    # sy_planets_flag is always populated ("Y"/"N") in DI_STARS_EXEP for this
    # target list, so this is a field-populated check, not a "companion
    # search was actually performed" or "observation exists" check -- a
    # star flagged "N" has not necessarily ever been surveyed for
    # companions. Deliberately EXCLUDED from evidence_completeness (see
    # NON_COVERAGE_CATEGORY_KEYS below) so it cannot silently inflate the
    # completeness score for every star. Kept as its own tracked column
    # because it would still expose a real gap if the upstream field ever
    # went unpopulated.
    return pd.notna(row.get("sy_planets_flag"))


def _exozodi_present(row: pd.Series) -> bool:
    # Same caveat as _rv_companion_present: a populated sy_disks_flag means
    # the archive recorded *some* answer (which may be "no excess
    # reported"), not that a dedicated exozodiacal-dust observation (e.g.
    # HOSTS) exists for this star. Excluded from evidence_completeness for
    # the same reason.
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
        "archive_planet_flag_populated",
        "Known-planet flag field is populated (sy_planets_flag not null) -- "
        "does NOT mean a companion search was performed; see LIMITATIONS.md",
        _rv_companion_present,
    ),
    EvidenceCategory(
        "archive_disk_flag_populated",
        "Circumstellar-disk flag field is populated (sy_disks_flag not null) "
        "-- does NOT mean a dedicated exozodi observation exists; see LIMITATIONS.md",
        _exozodi_present,
    ),
    EvidenceCategory(
        "astrometric_acceleration",
        "Star has a Hipparcos-Gaia Catalog of Accelerations (HGCA) entry",
        _astrometric_accel_present,
    ),
]

# Categories that record "does the archive have a populated field" rather
# than "does a real observation/survey exist for this star" -- excluded from
# evidence_completeness so a universally-populated metadata field cannot
# silently inflate every star's score. See docs/LIMITATIONS.md.
NON_COVERAGE_CATEGORY_KEYS = {"archive_planet_flag_populated", "archive_disk_flag_populated"}
COVERAGE_CATEGORIES = [c for c in EVIDENCE_CATEGORIES if c.key not in NON_COVERAGE_CATEGORY_KEYS]


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
    merged["hgca_accel_qvalue"] = _benjamini_hochberg_qvalues(merged["hgca_accel_pvalue"])
    merged["hgca_significant_accel_fdr"] = merged["hgca_accel_qvalue"] < ACCEL_SIGNIFICANCE_ALPHA

    for cat in EVIDENCE_CATEGORIES:
        merged[cat.key] = merged.apply(cat.present_fn, axis=1)

    # evidence_completeness deliberately averages only COVERAGE_CATEGORIES,
    # not all of EVIDENCE_CATEGORIES: the excluded categories record a
    # universally-populated archive field, not real observational coverage
    # (see NON_COVERAGE_CATEGORY_KEYS above) and would otherwise silently
    # inflate every star's score by a fixed amount.
    all_cat_cols = [c.key for c in EVIDENCE_CATEGORIES]
    coverage_cat_cols = [c.key for c in COVERAGE_CATEGORIES]
    merged["evidence_completeness"] = merged[coverage_cat_cols].mean(axis=1)

    id_cols = ["target_id", "hip_name", "hd_name", "hip_number", "sy_dist",
               "sy_planets_flag", "sy_disks_flag"]
    return merged[id_cols + all_cat_cols + [
        "evidence_completeness", "hgca_chi2", "hgca_accel_pvalue",
        "hgca_significant_accel", "hgca_accel_qvalue", "hgca_significant_accel_fdr",
    ]]


def _benjamini_hochberg_qvalues(pvalues: pd.Series) -> pd.Series:
    """Benjamini-Hochberg FDR-adjusted q-values, computed only over the
    non-null p-values (stars with an HGCA cross-match); null entries stay
    null. Standard step-up procedure (Benjamini & Hochberg 1995); no new
    dependency needed for a ~10-line, well-known algorithm."""
    valid = pvalues.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=pvalues.index)
    n = len(valid)
    order = valid.sort_values().index
    ranks = np.arange(1, n + 1)
    raw_q = valid.loc[order].to_numpy() * n / ranks
    # enforce monotonicity (step-up): q-value can only increase as rank decreases
    q_monotone = np.minimum.accumulate(raw_q[::-1])[::-1]
    q_monotone = np.clip(q_monotone, 0.0, 1.0)
    qvalues = pd.Series(np.nan, index=pvalues.index)
    qvalues.loc[order] = q_monotone
    return qvalues
