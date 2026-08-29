import numpy as np
import pandas as pd
import pytest

from hwoevidence.evidence import (
    ACCEL_SIGNIFICANCE_ALPHA,
    COVERAGE_CATEGORIES,
    EVIDENCE_CATEGORIES,
    build_evidence_matrix,
)


def _star_row(**overrides):
    row = {
        "target_id": 0,
        "hip_name": "HIP 1", "hd_name": "HD 1", "hip_number": 1,
        "sy_dist": 10.0, "sy_planets_flag": "N", "sy_disks_flag": "N",
        "st_teff": 5700, "st_mass": 1.0, "st_rad": 1.0, "st_logg": 4.4,
        "st_log_rhk": -4.9, "wds_designation": None,
    }
    row.update(overrides)
    return row


def test_stellar_parameters_category_requires_all_four_fields():
    complete = pd.Series(_star_row())
    incomplete = pd.Series(_star_row(st_mass=None))
    fn = next(c for c in EVIDENCE_CATEGORIES if c.key == "stellar_parameters").present_fn
    assert fn(complete) is True
    assert fn(incomplete) is False


def test_multiplicity_present_only_with_wds_entry():
    with_wds = pd.Series(_star_row(wds_designation="01234+5678"))
    without_wds = pd.Series(_star_row(wds_designation=None))
    fn = next(c for c in EVIDENCE_CATEGORIES if c.key == "multiplicity").present_fn
    assert fn(with_wds) is True
    assert fn(without_wds) is False


def test_build_evidence_matrix_row_count_matches_input_exactly():
    """Regression test: a wide binary with both components sharing one HIP
    number previously fanned out the merge if the HGCA table also had a
    duplicate row for that HIP (see cli.py / evidence.py comments)."""
    stars = pd.DataFrame([_star_row(target_id=0, hip_name="HIP 99 A", hip_number=99),
                           _star_row(target_id=1, hip_name="HIP 99 B", hip_number=99)])
    hgca = pd.DataFrame([{"HIP": 99, "chi2": 5.0}, {"HIP": 99, "chi2": 5.0}])  # duplicated on purpose
    evidence = build_evidence_matrix(stars, hgca)
    assert len(evidence) == 2


def test_hgca_significance_matches_chi2_survival_function():
    stars = pd.DataFrame([_star_row(hip_number=1)])
    hgca = pd.DataFrame([{"HIP": 1, "chi2": 20.0}])  # well above the 2-dof threshold
    evidence = build_evidence_matrix(stars, hgca)
    from scipy.stats import chi2 as chi2_dist
    expected_p = chi2_dist.sf(20.0, df=2)
    assert evidence.loc[0, "hgca_accel_pvalue"] == pytest.approx(expected_p)
    assert evidence.loc[0, "hgca_significant_accel"] == (expected_p < ACCEL_SIGNIFICANCE_ALPHA)


def test_missing_hgca_entry_gives_no_acceleration_evidence():
    stars = pd.DataFrame([_star_row(hip_number=1)])
    hgca = pd.DataFrame(columns=["HIP", "chi2"])
    evidence = build_evidence_matrix(stars, hgca)
    assert not evidence.loc[0, "astrometric_acceleration"]
    assert np.isnan(evidence.loc[0, "hgca_accel_pvalue"])


def test_evidence_completeness_is_fraction_of_categories_present():
    stars = pd.DataFrame([_star_row(hip_number=1, wds_designation="x")])
    hgca = pd.DataFrame([{"HIP": 1, "chi2": 1.0}])
    evidence = build_evidence_matrix(stars, hgca)
    n_cats = len(EVIDENCE_CATEGORIES)
    # every category is present in this fixture row
    assert evidence.loc[0, "evidence_completeness"] == pytest.approx(1.0)
    assert n_cats == 6
    assert len(COVERAGE_CATEGORIES) == 4


def test_archive_flag_populated_categories_excluded_from_completeness():
    """Regression test for the always-populated-category bug: sy_planets_flag
    and sy_disks_flag are populated for essentially every row regardless of
    whether any real observation exists, so they must NOT count toward
    evidence_completeness (see NON_COVERAGE_CATEGORY_KEYS)."""
    # Only archive_planet_flag_populated and archive_disk_flag_populated are
    # present; every real coverage category is absent.
    stars = pd.DataFrame([_star_row(
        hip_number=1, sy_planets_flag="N", sy_disks_flag="N",
        st_teff=None, st_mass=None, st_rad=None, st_logg=None,
        st_log_rhk=None, wds_designation=None,
    )])
    hgca = pd.DataFrame(columns=["HIP", "chi2"])  # no HGCA entry either
    evidence = build_evidence_matrix(stars, hgca)
    assert evidence.loc[0, "archive_planet_flag_populated"]
    assert evidence.loc[0, "archive_disk_flag_populated"]
    assert evidence.loc[0, "evidence_completeness"] == pytest.approx(0.0)


def test_bh_qvalues_hand_calculation():
    """Benjamini-Hochberg on a classic hand-checkable 4-star case: p-values
    (0.01, 0.04, 0.03, 0.20) sorted are (0.01, 0.03, 0.04, 0.20) at ranks
    1-4/n=4, giving raw q = p*n/rank = (0.04, 0.06, 0.0533..., 0.20).
    Step-up monotonic enforcement (each q pulled down to the min of itself
    and every q at a larger p-value) gives final q = (0.04, 0.0533...,
    0.0533..., 0.20): rank 2's raw 0.06 is pulled down to rank 3's 0.0533
    (the smaller of the two), but rank 1's 0.04 is already below both and
    stays put."""
    stars = pd.DataFrame([
        _star_row(target_id=0, hip_number=1),
        _star_row(target_id=1, hip_number=2),
        _star_row(target_id=2, hip_number=3),
        _star_row(target_id=3, hip_number=4),
    ])
    from scipy.stats import chi2 as chi2_dist
    target_p = [0.01, 0.04, 0.03, 0.20]
    chi2_vals = [chi2_dist.isf(p, df=2) for p in target_p]
    hgca = pd.DataFrame([{"HIP": i + 1, "chi2": c} for i, c in enumerate(chi2_vals)])
    evidence = build_evidence_matrix(stars, hgca)
    q = evidence.sort_values("target_id")["hgca_accel_qvalue"].to_numpy()
    assert q == pytest.approx([0.04, 4 / 75, 4 / 75, 0.20], abs=1e-3)
