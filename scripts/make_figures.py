"""Regenerate publication figures from committed tabular results."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"
NAVY = "#1e3a5f"
BLUE = "#2563a6"
GOLD = "#b45309"
INK = "#172033"


def _style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "axes.spines.top": False,
        "axes.spines.right": False, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK, "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def coverage_figure() -> None:
    summary = pd.read_csv(RESULTS_DIR / "coverage_summary.csv")
    labels = ["Stellar\nparameters", "Activity\nlog R′HK", "Multiplicity\nWDS record", "HGCA\nentry"]
    values = summary["fraction_present"].to_numpy()
    counts = summary["n_present"].astype(int).to_numpy()
    total = int(summary["n_total"].iloc[0])
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    bars = ax.bar(labels, values, color=[NAVY, NAVY, GOLD, BLUE], width=0.62)
    for bar, value, count in zip(bars, values, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.018,
                f"{count}/{total}\n{value:.1%}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 1.13)
    ax.set_ylabel("Fraction of targets with catalogue evidence")
    ax.set_title("Observational-evidence coverage across 164 HWO candidate stars", loc="left", weight="bold")
    ax.text(0, -0.23, "WDS absence is not evidence that a star is single; coverage records catalogue presence only.",
            transform=ax.transAxes, fontsize=8.5, color="#475569")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "coverage_by_category.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def structure_figure() -> None:
    strata = pd.read_csv(RESULTS_DIR / "distance_strata.csv").iloc[:3]
    patterns = pd.read_csv(RESULTS_DIR / "missingness_patterns.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})
    keys = ["stellar_parameters_fraction", "activity_fraction", "multiplicity_fraction", "astrometric_acceleration_fraction"]
    labels = ["Stellar parameters", "Activity", "WDS record", "HGCA entry"]
    colors = [NAVY, "#4f6f91", GOLD, BLUE]
    x = np.arange(len(strata))
    width = 0.19
    for offset, (key, label, color) in enumerate(zip(keys, labels, colors)):
        ax1.bar(x + (offset - 1.5) * width, strata[key], width, label=label, color=color)
    ax1.set_xticks(x, [f"{label}\n(n={n})" for label, n in zip(strata["distance_stratum"], strata["n_targets"])])
    ax1.set_ylim(0, 1.08)
    ax1.set_ylabel("Coverage fraction")
    ax1.set_title("Coverage within cumulative distance cuts", loc="left", weight="bold")
    ax1.legend(frameon=False, fontsize=8, ncol=2, loc="lower left")

    pattern_labels = []
    for _, row in patterns.iterrows():
        missing = []
        if not row["activity"]:
            missing.append("activity")
        if not row["multiplicity"]:
            missing.append("WDS")
        if not row["astrometric_acceleration"]:
            missing.append("HGCA")
        pattern_labels.append("Complete" if not missing else "Missing " + " + ".join(missing))
    y = np.arange(len(patterns))
    ax2.barh(y, patterns["n_targets"], color=[NAVY] + [GOLD] * (len(patterns) - 1))
    ax2.set_yticks(y, pattern_labels)
    ax2.invert_yaxis()
    ax2.set_xlabel("Number of targets")
    ax2.set_title("Exact missingness patterns", loc="left", weight="bold")
    for index, count in enumerate(patterns["n_targets"]):
        ax2.text(count + 1, index, str(int(count)), va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "coverage_structure.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def acceleration_figure() -> None:
    evidence = pd.read_csv(RESULTS_DIR / "evidence_matrix.csv")
    matched = evidence[evidence["hgca_accel_pvalue"].notna()].sort_values("hgca_accel_pvalue")
    x = np.arange(1, len(matched) + 1)
    # Extremely large catalogue chi-squared values underflow the survival
    # function to exactly zero. Cap only the display at 20 dex; the CSV
    # retains the unmodified p-values and chi-squared statistics.
    y = np.minimum(-np.log10(np.clip(matched["hgca_accel_pvalue"].to_numpy(), 1e-300, 1)), 20)
    colors = np.where(matched["sy_planets_flag"].eq("N"), GOLD, BLUE)
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.scatter(x, y, c=colors, s=22, alpha=0.82, edgecolors="none")
    ax.axhline(2, color=NAVY, linestyle="--", linewidth=1.2, label="raw p = 0.01")
    ax.set_xlabel("HGCA-matched targets, ordered by p-value")
    ax.set_ylabel("−log₁₀(p), capped at 20 for display")
    ax.set_title("Astrometric acceleration is a follow-up signal, not a companion classification", loc="left", weight="bold")
    ax.legend(frameon=False)
    ax.text(0, -0.22, "Gold: no planet listed in the archive. Blue: ≥1 archive-listed planet. Colour does not identify the acceleration source.",
            transform=ax.transAxes, fontsize=8.5, color="#475569")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "hgca_acceleration_evidence.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    _style()
    coverage_figure()
    structure_figure()
    acceleration_figure()
    print(f"Wrote three figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
