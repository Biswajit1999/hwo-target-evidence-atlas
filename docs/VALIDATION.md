# Validation

| Check | Method | Test / evidence | Result (2026-08-28) |
|---|---|---|---|
| `DI_STARS_EXEP` row count matches the published target-list size | Live query against the NASA Exoplanet Archive | `tests/test_data_adapter.py::test_live_di_stars_exep_has_164_rows` | 164 rows, matches Mamajek & Stapelfeldt (2024) exactly |
| Known real system sanity check | HD 75732 A (55 Cancri, a well-known multi-planet system) has `sy_planets_flag == "Y"` | `tests/test_data_adapter.py::test_di_stars_excerpt_has_expected_real_values` | Pass |
| HGCA VOTABLE parser | Parses a real, verbatim per-star response fragment correctly (HIP, Gaia ID, chi2, proper motions) | `tests/test_data_adapter.py::test_parse_hgca_votable_row_real_fragment` | Pass |
| HGCA live cross-match | Live query for a real star returns exactly the expected HIP | `tests/test_data_adapter.py::test_live_hgca_cross_match` | Pass |
| Evidence-matrix row-count integrity | Merge must never change the number of rows, even with duplicate join keys | `tests/test_evidence.py::test_build_evidence_matrix_row_count_matches_input_exactly` (regression test) + a runtime `assert` in `evidence.build_evidence_matrix` | Pass; see "Bug found" below |
| Chi-squared-to-p-value conversion | Matches `scipy.stats.chi2.sf(chi2, df=2)` directly | `tests/test_evidence.py::test_hgca_significance_matches_chi2_survival_function` | Pass |
| Conflict detection logic | Flags only (significant acceleration) AND (no known companion); does not flag either condition alone | `tests/test_conflicts.py` (4 cases) | Pass |
| Ranking views stay separate | `combined_view` never produces a merged score column; a synthetic "high value, low evidence" star ranks #1 by value and worst by evidence simultaneously | `tests/test_ranking.py::test_combined_view_keeps_two_separate_rank_columns_not_merged` | Pass |

## Bug found and fixed before publication

Running the full pipeline against live data (not just the test suite)
before publishing surfaced a real bug: `DI_STARS_EXEP` contains five wide
binary systems whose two components share one Hipparcos number (e.g. Xi
Boo A/B, both `HIP 72659`). The first version of `load_hgca_for_hip`
queried VizieR once per *row* rather than once per *unique* HIP number,
producing a duplicated HGCA row for each such pair; the subsequent merge
in `build_evidence_matrix` then fanned out (2 star rows x 2 duplicate HGCA
rows = 4 output rows instead of 2), silently inflating the evidence
matrix from 164 to 172 rows. Fixed by deduplicating the HIP query list in
`cli.py` and adding a defensive `drop_duplicates` plus a runtime row-count
`assert` in `evidence.build_evidence_matrix`, with a regression test
reproducing the exact scenario
(`tests/test_evidence.py::test_build_evidence_matrix_row_count_matches_input_exactly`).

## Explicitly not yet validated

- No independent cross-check of the chi-squared-to-acceleration-detection
  interpretation against a second HGCA-based companion-detection study.
- No manual literature check, star by star, of the 31 flagged "undisclosed
  companion" conflicts -- they are reported as candidates for follow-up,
  not individually verified against the literature in this version.

## Reproducing these checks

```bash
pytest -q               # fixture-based, no network, < 5 s
pytest -q -m network      # + 2 live-service checks
```
