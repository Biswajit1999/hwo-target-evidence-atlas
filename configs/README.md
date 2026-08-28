# configs/

This project has no parameter grid to configure -- unlike a synthetic
injection-recovery study, `hwoevidence build` runs one deterministic
cross-match against two live catalogs (see `docs/REPRODUCIBILITY.md`). The
one tunable value, the HGCA acceleration significance threshold, is a
documented module constant (`ACCEL_SIGNIFICANCE_ALPHA` in
`src/hwoevidence/evidence.py`) rather than a config file, since changing it
has no other moving parts to coordinate.
