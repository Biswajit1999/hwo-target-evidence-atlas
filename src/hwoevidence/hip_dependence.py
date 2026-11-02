"""Audit non-independent HGCA tests and conditional HWO coverage contrasts.

The HGCA acceleration statistic is indexed by Hipparcos source, while the
HWO evidence matrix is indexed by target. Binary components can therefore
repeat the same p-value. No catalog or planet detection is inferred here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


def _hip_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated Hipparcos measurements without merging target identities."""
    if frame["hip_number"].isna().any():
        raise ValueError("missing Hipparcos identifier: cannot define independent test family")
    rows = []
    for hip, group in frame.groupby("hip_number", sort=True, dropna=False):
        p = pd.to_numeric(group["hgca_accel_pvalue"], errors="coerce")
        if p.notna().any() and p.isna().any():
            raise ValueError(f"inconsistent HGCA availability for HIP {hip}")
        if p.notna().any() and not np.allclose(p.to_numpy(), p.iloc[0], rtol=1e-12, atol=0):
            raise ValueError(f"inconsistent HGCA p-values for HIP {hip}")
        if not group["multiplicity"].astype(str).nunique() == 1:
            raise ValueError(f"inconsistent WDS coverage for HIP {hip}")
        rows.append({
            "hip_number": hip,
            "n_targets": len(group),
            "pvalue": float(p.iloc[0]) if p.notna().any() else np.nan,
            "multiplicity": str(group["multiplicity"].iloc[0]).lower() == "true",
            "distance_pc": float(pd.to_numeric(group["sy_dist"]).median()),
        })
    return pd.DataFrame(rows)


def _bh_qvalues(pvalues: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values for one independent-test family."""
    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("p-values must be a finite one-dimensional array in [0, 1]")
    if not len(p):
        return p.copy()
    order = np.argsort(p, kind="stable")
    q_sorted = np.minimum.accumulate((p[order] * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    q = np.empty_like(p)
    q[order] = np.clip(q_sorted, 0, 1)
    return q


def hip_fdr_audit(frame: pd.DataFrame, alpha: float = 0.01) -> dict:
    """Compare target-row BH flags against BH on unique HIP hypotheses."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    hips = _hip_table(frame)
    tested = hips["pvalue"].notna()
    hips["hip_qvalue"] = np.nan
    hips.loc[tested, "hip_qvalue"] = _bh_qvalues(hips.loc[tested, "pvalue"].to_numpy())
    q_by_hip = hips.set_index("hip_number")["hip_qvalue"]
    target_q = frame["hip_number"].map(q_by_hip)
    old = frame["hgca_significant_accel_fdr"].astype(str).str.lower().eq("true")
    new = target_q.le(alpha).fillna(False)
    changed = frame.loc[old != new, ["target_id", "hip_number", "hd_name"]]
    return {
        "n_target_rows": int(len(frame)),
        "n_unique_hip": int(len(hips)),
        "n_hgca_target_tests": int(frame["hgca_accel_pvalue"].notna().sum()),
        "n_unique_hgca_tests": int(tested.sum()),
        "n_original_fdr_target_flags": int(old.sum()),
        "n_hip_fdr_unique_flags": int(hips["hip_qvalue"].le(alpha).sum()),
        "n_hip_fdr_target_flags": int(new.sum()),
        "changed_target_ids": changed["target_id"].tolist(),
        "changed_hip_numbers": changed["hip_number"].tolist(),
        "n_duplicated_hip": int((hips["n_targets"] > 1).sum()),
    }


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    if trials == 0:
        return [float("nan"), float("nan")]
    p = successes / trials
    denom = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denom
    half = z * np.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denom
    return [float(centre - half), float(centre + half)]


def _contrast(mask: np.ndarray, covered: np.ndarray) -> dict:
    a = int(np.sum(mask & covered))
    b = int(np.sum(mask & ~covered))
    c = int(np.sum(~mask & covered))
    d = int(np.sum(~mask & ~covered))
    odds, pvalue = fisher_exact([[a, b], [c, d]], alternative="two-sided")
    return {
        "group_a_present": a, "group_a_total": a + b,
        "group_b_present": c, "group_b_total": c + d,
        "group_a_wilson95": _wilson(a, a + b),
        "group_b_wilson95": _wilson(c, c + d),
        "fisher_odds_ratio": float(odds), "fisher_two_sided_p": float(pvalue),
    }


def wds_distance_contrast(frame: pd.DataFrame, boundary_pc: float = 10.0) -> dict:
    """Disjoint near/far WDS catalogue-presence contrast at unique-HIP level."""
    if not np.isfinite(boundary_pc) or boundary_pc <= 0:
        raise ValueError("boundary_pc must be positive and finite")
    hips = _hip_table(frame)
    valid = np.isfinite(hips["distance_pc"].to_numpy())
    if not valid.all():
        raise ValueError("missing distance cannot be assigned to a stratum")
    result = _contrast(
        hips["distance_pc"].to_numpy() <= boundary_pc,
        hips["multiplicity"].to_numpy(dtype=bool),
    )
    return {"near_boundary_pc": boundary_pc, **result}


def wds_acceleration_contrast(frame: pd.DataFrame, alpha: float = 0.01) -> dict:
    """WDS record presence conditional on HIP-level HGCA FDR, not companion type."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    hips = _hip_table(frame)
    hips = hips[hips["pvalue"].notna()].copy()
    hips["q"] = _bh_qvalues(hips["pvalue"].to_numpy())
    result = _contrast(
        hips["q"].to_numpy() <= alpha,
        hips["multiplicity"].to_numpy(dtype=bool),
    )
    return {"n_unique_hgca_tests": len(hips), "alpha": alpha, **result}
