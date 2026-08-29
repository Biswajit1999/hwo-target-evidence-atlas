import pandas as pd

from hwoevidence.ranking import combined_view, rank_by_evidence_completeness, rank_by_science_value


def _stars():
    return pd.DataFrame([
        {"target_id": 0, "hip_name": "HIP 1", "hd_name": "HD 1", "sy_dist": 20.0},
        {"target_id": 1, "hip_name": "HIP 2", "hd_name": "HD 2", "sy_dist": 5.0},
        {"target_id": 2, "hip_name": "HIP 3", "hd_name": "HD 3", "sy_dist": 12.0},
    ])


def _evidence():
    return pd.DataFrame([
        {"target_id": 0, "hip_name": "HIP 1", "evidence_completeness": 1.0},
        {"target_id": 1, "hip_name": "HIP 2", "evidence_completeness": 0.2},
        {"target_id": 2, "hip_name": "HIP 3", "evidence_completeness": 0.6},
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
    assert "distance_rank" in view.columns
    assert "evidence_completeness_rank" in view.columns
    assert "combined_score" not in view.columns
    # closest star (HIP 2) also happens to have the worst evidence here --
    # exactly the "high value, low evidence" case the two-column design
    # exists to surface, not hide.
    hip2 = view[view["hip_name"] == "HIP 2"].iloc[0]
    assert hip2["distance_rank"] == 1
    assert hip2["evidence_completeness_rank"] == 3


def test_combined_view_does_not_fan_out_on_shared_hip_name():
    """Regression test: two wide-binary components sharing one hip_name
    (e.g. HIP 72659 A/B) previously fanned out the merge in combined_view
    because it joined on hip_name instead of the unique target_id -- 164
    stars produced 174 ranking rows in the original release. See
    ranking.py's combined_view docstring."""
    stars = pd.DataFrame([
        {"target_id": 0, "hip_name": "HIP 99", "hd_name": "HD 99 A", "sy_dist": 10.0},
        {"target_id": 1, "hip_name": "HIP 99", "hd_name": "HD 99 B", "sy_dist": 11.0},
    ])
    evidence = pd.DataFrame([
        {"target_id": 0, "evidence_completeness": 0.5},
        {"target_id": 1, "evidence_completeness": 0.75},
    ])
    view = combined_view(stars, evidence)
    assert len(view) == 2
    assert sorted(view["hd_name"]) == ["HD 99 A", "HD 99 B"]
