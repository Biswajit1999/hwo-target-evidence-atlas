"""Command-line workflow for the HWO target evidence cross-match."""
from __future__ import annotations

from pathlib import Path

import click

from .conflicts import find_undisclosed_companion_conflicts
from .data import CachePaths, load_di_stars_exep, load_hgca_for_hip
from .evidence import build_evidence_matrix
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

    conflicts = find_undisclosed_companion_conflicts(evidence)
    conflicts.to_csv(out / "conflicts.csv", index=False)
    click.echo(f"Wrote {out/'conflicts.csv'} ({len(conflicts)} candidate conflicts)")

    ranking = combined_view(stars, evidence)
    ranking.to_csv(out / "ranking.csv", index=False)
    click.echo(f"Wrote {out/'ranking.csv'}")

    summary = evidence[[c for c in evidence.columns if c not in
                         ("hip_name", "hd_name", "hip_number")]].select_dtypes(include="bool").mean()
    click.echo("\nPer-category evidence completeness (fraction of 164 targets):")
    for k, v in summary.items():
        click.echo(f"  {k}: {v:.1%}")


if __name__ == "__main__":
    main()
