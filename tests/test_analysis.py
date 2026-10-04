import pandas as pd

from hwoevidence.analysis import (
    coverage_summary,
    distance_stratified_coverage,
    missingness_patterns,
    summary_payload,
)


def _evidence():
    return pd.DataFrame([
        {"sy_dist": 5.0, "stellar_parameters": True, "activity": True,
         "multiplicity": False, "astrometric_acceleration": True,
         "evidence_completeness": 0.75, "hgca_accel_pvalue": 0.001,
         "hgca_significant_accel": True, "hgca_significant_accel_fdr": True,
         "sy_planets_flag": "N"},
        {"sy_dist": 25.0, "stellar_parameters": True, "activity": False,
         "multiplicity": False, "astrometric_acceleration": False,
         "evidence_completeness": 0.25, "hgca_accel_pvalue": float("nan"),
         "hgca_significant_accel": False, "hgca_significant_accel_fdr": False,
         "sy_planets_flag": "Y"},
    ])


def test_coverage_summary_reports_exact_denominators():
    summary = coverage_summary(_evidence()).set_index("category")
    assert summary.loc["stellar_parameters", "n_present"] == 2
    assert summary.loc["activity", "fraction_present"] == 0.5


def test_missingness_patterns_preserve_boolean_categories():
    patterns = missingness_patterns(_evidence())
    assert patterns["n_targets"].sum() == 2
    assert set(patterns["n_categories_present"]) == {1, 3}


def test_distance_strata_are_cumulative():
    strata = distance_stratified_coverage(_evidence()).set_index("distance_stratum")
    assert strata.loc["<=10 pc", "n_targets"] == 1
    assert strata.loc["<=30 pc", "n_targets"] == 2


def test_summary_names_actual_bh_test_family():
    payload = summary_payload(_evidence())
    assert payload["n_targets"] == 2
    assert payload["n_hgca_tests"] == 1
    assert payload["fdr_family"] == "non-null HGCA cross-matches"
