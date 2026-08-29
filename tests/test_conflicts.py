import pandas as pd

from hwoevidence.conflicts import (
    find_hgca_accelerators_without_archive_listed_planets,
    find_missing_evidence,
)


def _evidence_row(**overrides):
    row = {
        "target_id": 0, "hip_name": "HIP 1", "hd_name": "HD 1", "sy_planets_flag": "N",
        "hgca_chi2": 20.0, "hgca_accel_pvalue": 1e-5, "hgca_significant_accel": True,
        "hgca_accel_qvalue": 1e-5, "hgca_significant_accel_fdr": True,
        "multiplicity": True,
    }
    row.update(overrides)
    return row


def test_flags_significant_accel_with_no_archive_listed_planet():
    df = pd.DataFrame([_evidence_row()])
    result = find_hgca_accelerators_without_archive_listed_planets(df)
    assert len(result) == 1


def test_does_not_flag_when_planet_already_archive_listed():
    df = pd.DataFrame([_evidence_row(sy_planets_flag="Y")])
    result = find_hgca_accelerators_without_archive_listed_planets(df)
    assert len(result) == 0


def test_does_not_flag_when_acceleration_not_significant():
    df = pd.DataFrame([_evidence_row(hgca_significant_accel=False)])
    result = find_hgca_accelerators_without_archive_listed_planets(df)
    assert len(result) == 0


def test_does_not_flag_when_no_hgca_entry_at_all():
    df = pd.DataFrame([_evidence_row(hgca_significant_accel=None)])
    result = find_hgca_accelerators_without_archive_listed_planets(df)
    assert len(result) == 0


def test_find_missing_evidence():
    df = pd.DataFrame([
        _evidence_row(hip_name="HIP 1", multiplicity=True),
        _evidence_row(hip_name="HIP 2", multiplicity=False),
    ])
    missing = find_missing_evidence(df, "multiplicity")
    assert list(missing["hip_name"]) == ["HIP 2"]
