import numpy as np
import pandas as pd
import pytest

from hwoevidence.hip_dependence import (
    _bh_qvalues,
    _hip_table,
    hip_fdr_audit,
    wds_acceleration_contrast,
    wds_distance_contrast,
)


def _fixture():
    return pd.DataFrame([
        {"target_id": "a", "hip_number": 1, "hd_name": "A", "sy_dist": 5.0,
         "multiplicity": True, "hgca_accel_pvalue": 0.001,
         "hgca_significant_accel_fdr": True},
        {"target_id": "b", "hip_number": 1, "hd_name": "B", "sy_dist": 5.1,
         "multiplicity": True, "hgca_accel_pvalue": 0.001,
         "hgca_significant_accel_fdr": True},
        {"target_id": "c", "hip_number": 2, "hd_name": "C", "sy_dist": 15.0,
         "multiplicity": False, "hgca_accel_pvalue": 0.5,
         "hgca_significant_accel_fdr": False},
        {"target_id": "d", "hip_number": 3, "hd_name": "D", "sy_dist": 20.0,
         "multiplicity": True, "hgca_accel_pvalue": np.nan,
         "hgca_significant_accel_fdr": False},
    ])


def test_bh_known_values_and_monotonicity():
    np.testing.assert_allclose(_bh_qvalues([0.01, 0.04, 0.03, 0.8]), [0.04, 0.05333333333333334, 0.05333333333333334, 0.8])


def test_bh_empty_and_invalid():
    assert _bh_qvalues([]).size == 0
    with pytest.raises(ValueError):
        _bh_qvalues([0.2, np.nan])


def test_duplicate_measurement_counted_once():
    audit = hip_fdr_audit(_fixture())
    assert audit["n_target_rows"] == 4
    assert audit["n_unique_hgca_tests"] == 2
    assert audit["n_duplicated_hip"] == 1
    assert audit["n_hip_fdr_unique_flags"] == 1
    assert audit["n_hip_fdr_target_flags"] == 2


def test_inconsistent_duplicate_pvalues_rejected():
    frame = _fixture()
    frame.loc[1, "hgca_accel_pvalue"] = 0.2
    with pytest.raises(ValueError, match="inconsistent HGCA p-values"):
        _hip_table(frame)


def test_inconsistent_duplicate_wds_rejected():
    frame = _fixture()
    frame.loc[1, "multiplicity"] = False
    with pytest.raises(ValueError, match="inconsistent WDS"):
        _hip_table(frame)


def test_wds_near_far_uses_unique_hip_and_disjoint_groups():
    result = wds_distance_contrast(_fixture(), boundary_pc=10)
    assert (result["group_a_present"], result["group_a_total"]) == (1, 1)
    assert (result["group_b_present"], result["group_b_total"]) == (1, 2)
    assert 0 <= result["fisher_two_sided_p"] <= 1


def test_acceleration_contrast_excludes_null_hgca():
    result = wds_acceleration_contrast(_fixture())
    assert result["n_unique_hgca_tests"] == 2
    assert result["group_a_total"] == 1
    assert result["group_b_total"] == 1


def test_invalid_alpha_and_distance_rejected():
    with pytest.raises(ValueError):
        hip_fdr_audit(_fixture(), alpha=0)
    with pytest.raises(ValueError):
        wds_distance_contrast(_fixture(), boundary_pc=-1)
