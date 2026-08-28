# Contributing

Bug reports, replication attempts, and scientific critique are welcome via
GitHub Issues and Discussions.

## Development setup

```bash
git clone https://github.com/Biswajit1999/hwo-target-evidence-atlas.git
cd hwo-target-evidence-atlas
python -m pip install -e ".[dev]"
pytest -q               # fast tests, fixture-based, no network
pytest -q -m network     # adds live NASA Exoplanet Archive + VizieR checks
```

## Before opening a pull request

- Run `pytest -q` and `ruff check src tests`; both must pass.
- If you add or change an evidence category, add a test that checks both
  the "present" and "absent" cases (see `tests/test_evidence.py`), and
  update `docs/METHODS.md`.
- If you add a data source, update `docs/DATA_SOURCES.md` with provider,
  URL, access date, and licence terms, and add an offline test fixture
  built from a small, real excerpt of that source (never a fabricated one).
- Keep commits small and focused on one logical change.

## Good first issues

See the repository Issues tab, including cross-matching additional evidence
sources (UV/X-ray archival detections, the HOSTS exozodi survey, RV
companion-mass limits from SPORES-HWO), and the open items in
`docs/LIMITATIONS.md`.
