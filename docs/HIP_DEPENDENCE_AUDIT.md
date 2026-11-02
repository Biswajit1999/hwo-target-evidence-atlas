# Independent-HIP evidence audit (2 November 2026)

Run `python scripts/hip_dependence_audit.py` from an editable install.

The pinned 164-target evidence matrix contains components sharing a Hipparcos
identifier. A shared HGCA acceleration p-value is one source-level measurement,
not independent evidence for each HWO target row. The audit recomputes
Benjamini–Hochberg q-values over non-null **unique HIP** measurements and
compares those flags to the frozen per-target result; it does not rewrite
published results. Identical repeated p-values are required, rather than
silently averaging conflicting measurements. This is a sensitivity analysis:
HGCA measurements can still be statistically dependent across different
Hipparcos sources, so BH's usual independence/positive-dependence conditions
are not independently established here.

Two descriptive, explicitly disjoint Fisher exact comparisons use one HIP
source per observation: WDS-record presence within/beyond 10 pc, and WDS
presence among FDR-significant versus nonsignificant HGCA sources. Wilson
intervals describe the corresponding catalogue-presence fractions. A missing
WDS record does **not** imply a single star; HGCA acceleration does **not**
identify a planet. These comparisons are exploratory, not preregistered
hypothesis tests or HWO target rankings. No new HOSTS exozodiacal data were
acquired; issue #3 remains open. The original target-level matrix is preserved.

Tests: `python -m pytest -q tests/test_hip_dependence.py`.
