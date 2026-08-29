"""Regenerate results/figures/ from the committed results/*.csv -- never
hand-edited. Run after ``hwoevidence build`` writes new results.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"

COVERAGE_KEYS = ["stellar_parameters", "activity", "multiplicity", "astrometric_acceleration"]
NON_COVERAGE_KEYS = ["archive_planet_flag_populated", "archive_disk_flag_populated"]
LABELS = {
    "stellar_parameters": "stellar parameters",
    "activity": "chromospheric activity",
    "multiplicity": "multiplicity (WDS)",
    "astrometric_acceleration": "HGCA acceleration",
    "archive_planet_flag_populated": "planet-flag field\npopulated (not coverage)",
    "archive_disk_flag_populated": "disk-flag field\npopulated (not coverage)",
}


def main() -> None:
    evidence = pd.read_csv(RESULTS_DIR / "evidence_matrix.csv")
    n = len(evidence)

    coverage_frac = [evidence[k].mean() for k in COVERAGE_KEYS]
    non_coverage_frac = [evidence[k].mean() for k in NON_COVERAGE_KEYS]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    all_keys = COVERAGE_KEYS + NON_COVERAGE_KEYS
    all_frac = coverage_frac + non_coverage_frac
    colors = ["#2a6f97"] * len(COVERAGE_KEYS) + ["#b0b0b0"] * len(NON_COVERAGE_KEYS)
    bars = ax.bar([LABELS[k] for k in all_keys], all_frac, color=colors)
    ax.axhline(evidence["evidence_completeness"].mean(), color="#d64550", linestyle="--",
               linewidth=1, label=f"mean evidence_completeness ({evidence['evidence_completeness'].mean():.1%}, "
                                    f"coverage categories only)")
    for bar, frac in zip(bars, all_frac):
        ax.text(bar.get_x() + bar.get_width() / 2, frac + 0.02, f"{frac:.1%}",
                ha="center", fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel(f"Fraction of {n} targets")
    ax.set_title("Per-category evidence: blue = real observational coverage,\n"
                  "gray = archive field populated (excluded from evidence_completeness)")
    ax.legend(loc="lower left", fontsize=8)
    plt.xticks(rotation=15, ha="right", fontsize=8)
    plt.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "evidence_completeness.png"
    fig.savefig(out, dpi=150)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
