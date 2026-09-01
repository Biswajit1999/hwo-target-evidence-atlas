"""Statistical summaries for catalog-field coverage fractions."""
from __future__ import annotations

import math

import pandas as pd

from .evidence import COVERAGE_CATEGORIES


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Two-sided Wilson interval for a binomial proportion."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    p = successes / trials
    denom = 1.0 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def coverage_summary(evidence: pd.DataFrame) -> pd.DataFrame:
    """Counts, fractions, and Wilson intervals for each declared field."""
    rows = []
    n = len(evidence)
    for category in COVERAGE_CATEGORIES:
        k = int(evidence[category.key].astype(bool).sum())
        low, high = wilson_interval(k, n)
        rows.append({
            "category": category.key,
            "n_targets": n,
            "n_with_catalog_field": k,
            "catalog_field_coverage_fraction": k / n,
            "ci95_low": low,
            "ci95_high": high,
        })
    return pd.DataFrame(rows)
