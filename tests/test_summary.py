import pandas as pd
import pytest

from hwoevidence.summary import coverage_summary, wilson_interval


def test_wilson_interval_contains_observed_fraction():
    low, high = wilson_interval(7, 10)
    assert low < 0.7 < high


def test_coverage_summary_retains_denominators_and_intervals():
    evidence = pd.DataFrame({
        "stellar_parameters": [True, True, False],
        "activity": [True, False, False],
        "multiplicity": [False, False, False],
        "astrometric_acceleration": [True, True, True],
    })
    summary = coverage_summary(evidence).set_index("category")
    assert summary.loc["stellar_parameters", "n_targets"] == 3
    assert summary.loc["stellar_parameters", "n_with_catalog_field"] == 2
    assert summary.loc["stellar_parameters", "catalog_field_coverage_fraction"] == pytest.approx(2 / 3)
    assert summary.loc["multiplicity", "ci95_high"] > 0
