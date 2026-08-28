import pandas as pd

from hwoevidence.conflicts import find_missing_evidence, find_undisclosed_companion_conflicts


def _evidence_row(**overrides):
    row = {
        "hip_name": "HIP 1", "hd_name": "HD 1", "sy_planets_flag": "N",
        "hgca_chi2": 20.0, "hgca_accel_pvalue": 1e-5, "hgca_significant_accel": True,
        "multiplicity": True,
    }
    row.update(overrides)
    return row


def test_flags_significant_accel_with_no_known_companion():
    df = pd.DataFrame([_evidence_row()])
    conflicts = find_undisclosed_companion_conflicts(df)
    assert len(conflicts) == 1


def test_does_not_flag_when_companion_already_known():
    df = pd.DataFrame([_evidence_row(sy_planets_flag="Y")])
    conflicts = find_undisclosed_companion_conflicts(df)
    assert len(conflicts) == 0


def test_does_not_flag_when_acceleration_not_significant():
    df = pd.DataFrame([_evidence_row(hgca_significant_accel=False)])
    conflicts = find_undisclosed_companion_conflicts(df)
    assert len(conflicts) == 0


def test_does_not_flag_when_no_hgca_entry_at_all():
    df = pd.DataFrame([_evidence_row(hgca_significant_accel=None)])
    conflicts = find_undisclosed_companion_conflicts(df)
    assert len(conflicts) == 0


def test_find_missing_evidence():
    df = pd.DataFrame([
        _evidence_row(hip_name="HIP 1", multiplicity=True),
        _evidence_row(hip_name="HIP 2", multiplicity=False),
    ])
    missing = find_missing_evidence(df, "multiplicity")
    assert list(missing["hip_name"]) == ["HIP 2"]
