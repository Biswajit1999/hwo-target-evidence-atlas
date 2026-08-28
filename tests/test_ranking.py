import pandas as pd

from hwoevidence.ranking import combined_view, rank_by_evidence_completeness, rank_by_science_value


def _stars():
    return pd.DataFrame([
        {"hip_name": "HIP 1", "hd_name": "HD 1", "sy_dist": 20.0},
        {"hip_name": "HIP 2", "hd_name": "HD 2", "sy_dist": 5.0},
        {"hip_name": "HIP 3", "hd_name": "HD 3", "sy_dist": 12.0},
    ])


def _evidence():
    return pd.DataFrame([
        {"hip_name": "HIP 1", "evidence_completeness": 1.0},
        {"hip_name": "HIP 2", "evidence_completeness": 0.2},
        {"hip_name": "HIP 3", "evidence_completeness": 0.6},
    ])


def test_rank_by_science_value_orders_by_distance_ascending():
    ranked = rank_by_science_value(_stars())
    assert list(ranked["hip_name"]) == ["HIP 2", "HIP 3", "HIP 1"]


def test_rank_by_evidence_completeness_orders_worst_first():
    ranked = rank_by_evidence_completeness(_evidence())
    assert ranked.iloc[0]["hip_name"] == "HIP 2"
    assert ranked.iloc[-1]["hip_name"] == "HIP 1"


def test_combined_view_keeps_two_separate_rank_columns_not_merged():
    view = combined_view(_stars(), _evidence())
    assert "science_value_rank" in view.columns
    assert "evidence_completeness_rank" in view.columns
    assert "combined_score" not in view.columns
    # closest star (HIP 2) also happens to have the worst evidence here --
    # exactly the "high value, low evidence" case the two-column design
    # exists to surface, not hide.
    hip2 = view[view["hip_name"] == "HIP 2"].iloc[0]
    assert hip2["science_value_rank"] == 1
    assert hip2["evidence_completeness_rank"] == 3
