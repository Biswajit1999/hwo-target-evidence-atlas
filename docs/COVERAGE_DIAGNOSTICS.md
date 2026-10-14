# HWO evidence-coverage diagnostics

This extension performs **three distinct, non-causal analyses** on `results/evidence_matrix.csv` without modifying the original coverage definition or ranking:

1. **Wilson binomial intervals** for each of the four actual observation/cross-match categories, retaining numerator and denominator. These intervals are descriptive: the 164 curated HWO targets are not a random sample of all stars.
2. **Disjoint distance strata** `(0,10], (10,20], (20,30], (30,∞]` pc, to avoid treating nested cumulative cuts as independent comparisons. Missing distances are counted separately.
3. **Pairwise missingness dependence** across the four categories using two-sided Fisher exact tests and Benjamini–Hochberg correction across six exploratory comparisons. An empty catalog cross-match is not evidence of astrophysical absence.

Run `python scripts/analyze_coverage_diagnostics.py --input results/evidence_matrix.csv --out results/coverage_diagnostics` after installing the project with `pip install -e .`. The command rejects duplicate target IDs and writes three CSVs and a provenance/caveat JSON summary. All tests are deterministic and fixture-based. No claims of new companions, observed exozodiacal dust, or causation are made. A large odds ratio may be undefined/infinite when a cell is zero, and selection bias cannot be removed by Fisher tests.
