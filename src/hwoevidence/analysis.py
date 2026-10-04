"""Transparent aggregate analyses for the HWO evidence matrix."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .evidence import ACCEL_SIGNIFICANCE_ALPHA, COVERAGE_CATEGORIES


def coverage_summary(evidence: pd.DataFrame) -> pd.DataFrame:
    """Counts and fractions for each non-bookkeeping evidence category."""
    rows = []
    total = len(evidence)
    for category in COVERAGE_CATEGORIES:
        count = int(evidence[category.key].fillna(False).astype(bool).sum())
        rows.append({
            "category": category.key,
            "description": category.description,
            "n_present": count,
            "n_total": total,
            "fraction_present": count / total if total else float("nan"),
        })
    return pd.DataFrame(rows)


def missingness_patterns(evidence: pd.DataFrame) -> pd.DataFrame:
    """Exact four-category coverage patterns, most common first."""
    columns = [category.key for category in COVERAGE_CATEGORIES]
    patterns = (
        evidence[columns].fillna(False).astype(bool)
        .value_counts(dropna=False).rename("n_targets").reset_index()
    )
    patterns["fraction_targets"] = patterns["n_targets"] / len(evidence)
    patterns["n_categories_present"] = patterns[columns].sum(axis=1)
    return patterns.sort_values(
        ["n_targets", "n_categories_present"], ascending=[False, False]
    ).reset_index(drop=True)


def distance_stratified_coverage(evidence: pd.DataFrame) -> pd.DataFrame:
    """Coverage within cumulative distance cuts; no blended target score."""
    columns = [category.key for category in COVERAGE_CATEGORIES]
    rows = []
    for label, limit in (("<=10 pc", 10.0), ("<=20 pc", 20.0), ("<=30 pc", 30.0), ("all", None)):
        subset = evidence if limit is None else evidence[evidence["sy_dist"] <= limit]
        row = {"distance_stratum": label, "max_distance_pc": limit, "n_targets": len(subset)}
        for column in columns:
            row[f"{column}_fraction"] = float(subset[column].mean()) if len(subset) else float("nan")
        row["mean_category_coverage"] = float(subset[columns].mean().mean()) if len(subset) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def summary_payload(evidence: pd.DataFrame) -> dict:
    """Machine-readable headline counts with explicit statistical denominator."""
    valid = evidence["hgca_accel_pvalue"].notna()
    no_planet = evidence["sy_planets_flag"].eq("N")
    return {
        "n_targets": len(evidence),
        "n_hgca_tests": int(valid.sum()),
        "fdr_family": "non-null HGCA cross-matches",
        "alpha": ACCEL_SIGNIFICANCE_ALPHA,
        "n_raw_significant": int(evidence["hgca_significant_accel"].fillna(False).sum()),
        "n_fdr_significant": int(evidence["hgca_significant_accel_fdr"].fillna(False).sum()),
        "n_raw_significant_without_archive_planet": int(
            (evidence["hgca_significant_accel"].fillna(False) & no_planet).sum()
        ),
        "n_fdr_significant_without_archive_planet": int(
            (evidence["hgca_significant_accel_fdr"].fillna(False) & no_planet).sum()
        ),
        "mean_category_coverage": float(evidence["evidence_completeness"].mean()),
    }


def write_analysis_products(evidence: pd.DataFrame, out: Path) -> dict:
    """Write all aggregate tables and return the JSON summary payload."""
    coverage_summary(evidence).to_csv(out / "coverage_summary.csv", index=False)
    missingness_patterns(evidence).to_csv(out / "missingness_patterns.csv", index=False)
    distance_stratified_coverage(evidence).to_csv(out / "distance_strata.csv", index=False)
    payload = summary_payload(evidence)
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
