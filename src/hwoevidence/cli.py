"""Command-line workflow for the HWO target evidence cross-match."""
from __future__ import annotations

from pathlib import Path

import click

from .analysis import write_analysis_products
from .conflicts import find_hgca_accelerators_without_archive_listed_planets
from .data import CachePaths, load_di_stars_exep, load_hgca_for_hip
from .evidence import COVERAGE_CATEGORIES, build_evidence_matrix
from .ranking import combined_view


@click.group()
def main() -> None:
    """hwoevidence: HWO target evidence-completeness cross-match."""


@main.command("build")
@click.option("--cache-dir", default="data/cache", show_default=True)
@click.option("--out", "out_dir", default="results", show_default=True)
@click.option("--force-refetch", is_flag=True, default=False)
def build_cmd(cache_dir: str, out_dir: str, force_refetch: bool) -> None:
    """Fetch both catalogs, build the evidence matrix, and write results."""
    paths = CachePaths(cache_dir=Path(cache_dir))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    stars = load_di_stars_exep(paths, force=force_refetch)
    click.echo(f"DI_STARS_EXEP: {len(stars)} rows")

    # Several targets are components of a wide binary sharing one Hipparcos
    # number (e.g. Xi Boo A/B both under HIP 72659); dedupe before querying
    # so each HIP is only fetched once (see evidence.build_evidence_matrix
    # for the corresponding defensive dedupe on the merge side).
    hip_numbers = sorted(set(stars["hip_number"].dropna().astype(int).tolist()))
    hgca = load_hgca_for_hip(hip_numbers, paths, force=force_refetch)
    click.echo(f"HGCA cross-match: {len(hgca)}/{len(hip_numbers)} stars matched")

    evidence = build_evidence_matrix(stars, hgca)
    evidence.to_csv(out / "evidence_matrix.csv", index=False)
    click.echo(f"Wrote {out/'evidence_matrix.csv'} ({len(evidence)} rows)")
    assert len(evidence) == len(stars), (
        f"evidence_matrix row count ({len(evidence)}) != star count ({len(stars)})"
    )

    conflicts = find_hgca_accelerators_without_archive_listed_planets(evidence)
    conflicts.to_csv(out / "hgca_accelerators_without_listed_planets.csv", index=False)
    click.echo(
        f"Wrote {out/'hgca_accelerators_without_listed_planets.csv'} "
        f"({len(conflicts)} HGCA accelerators lacking an archive-listed planet; "
        f"companion nature undetermined)"
    )

    ranking = combined_view(stars, evidence)
    ranking.to_csv(out / "ranking.csv", index=False)
    click.echo(f"Wrote {out/'ranking.csv'} ({len(ranking)} rows)")
    assert len(ranking) == len(stars), (
        f"ranking row count ({len(ranking)}) != star count ({len(stars)})"
    )

    payload = write_analysis_products(evidence, out)
    click.echo(
        f"Wrote aggregate analyses (BH family: {payload['n_hgca_tests']} "
        "non-null HGCA cross-matches)"
    )

    coverage_cols = [c.key for c in COVERAGE_CATEGORIES]
    summary = evidence[coverage_cols].mean()
    click.echo(f"\nPer-category observational coverage (fraction of {len(stars)} targets, "
               f"coverage categories only -- see docs/LIMITATIONS.md):")
    for k, v in summary.items():
        click.echo(f"  {k}: {v:.1%}")
    click.echo(f"\nOverall evidence_completeness (mean of coverage categories): "
               f"{evidence['evidence_completeness'].mean():.1%}")


if __name__ == "__main__":
    main()
