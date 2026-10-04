# Reproducibility

```bash
git clone https://github.com/Biswajit1999/hwo-target-evidence-atlas.git
cd hwo-target-evidence-atlas
python -m pip install -e ".[dev]"

hwoevidence build --cache-dir data/cache --out results/
python scripts/make_figures.py
```

This regenerates the per-target matrix, candidate list, ranking, aggregate
coverage tables, exact missingness patterns, distance strata, and JSON
summary from the versioned source snapshots (or from fresh NASA Exoplanet
Archive and VizieR queries with `--force-refetch`; see `docs/DATA_SOURCES.md`), and prints the
per-category completeness summary quoted in `README.md` and
`CHANGELOG.md`; `scripts/make_figures.py` regenerates
three publication figures from those CSVs. Source data is cached with a
SHA-256 checksum manifest in `data/cache/manifest.json`; cached reads fail
closed on a checksum mismatch. Re-runs do not query the network unless
`--force-refetch` is passed.

## Determinism

The evidence matrix, conflict list, and rankings are deterministic
functions of the two live catalogs' current contents -- there is no random
seed in this pipeline. Re-running against the same catalog snapshot
reproduces identical output; re-running months later may differ if either
catalog is updated upstream (this is expected and is exactly why every
fetch is checksummed and timestamped).
