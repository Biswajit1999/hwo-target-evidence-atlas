import numpy as np
import pandas as pd
import pytest

from hwoevidence.evidence import (
    ACCEL_SIGNIFICANCE_ALPHA,
    EVIDENCE_CATEGORIES,
    build_evidence_matrix,
)


def _star_row(**overrides):
    row = {
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
    stars = pd.DataFrame([_star_row(hip_name="HIP 99 A", hip_number=99),
                           _star_row(hip_name="HIP 99 B", hip_number=99)])
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
    assert evidence.loc[0, "astrometric_acceleration"] == False
    assert np.isnan(evidence.loc[0, "hgca_accel_pvalue"])


def test_evidence_completeness_is_fraction_of_categories_present():
    stars = pd.DataFrame([_star_row(hip_number=1, wds_designation="x")])
    hgca = pd.DataFrame([{"HIP": 1, "chi2": 1.0}])
    evidence = build_evidence_matrix(stars, hgca)
    n_cats = len(EVIDENCE_CATEGORIES)
    # every category is present in this fixture row
    assert evidence.loc[0, "evidence_completeness"] == pytest.approx(1.0)
    assert n_cats == 6
