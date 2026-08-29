# Validation

| Check | Method | Test / evidence | Result (2026-08-29) |
|---|---|---|---|
| `DI_STARS_EXEP` row count matches the published target-list size | Live query against the NASA Exoplanet Archive | `tests/test_data_adapter.py::test_live_di_stars_exep_has_164_rows` | 164 rows, matches Mamajek & Stapelfeldt (2024) exactly |
| Known real system sanity check | HD 75732 A (55 Cancri, a well-known multi-planet system) has `sy_planets_flag == "Y"` | `tests/test_data_adapter.py::test_di_stars_excerpt_has_expected_real_values` | Pass |
| HGCA VOTABLE parser | Parses real, verbatim per-star response fragments correctly (HIP, Gaia ID, chi2, proper motions), and raises rather than silently misparsing on a structural mismatch or missing FIELD definitions | `tests/test_data_adapter.py::test_parse_hgca_votable_row_real_fragment`, `test_parse_hgca_votable_row_raises_on_missing_field_definitions`, `test_parse_hgca_votable_row_raises_on_shape_mismatch` | Pass |
| HGCA live cross-match | Live query for a real star returns exactly the expected HIP | `tests/test_data_adapter.py::test_live_hgca_cross_match` | Pass |
| Evidence-matrix row-count integrity | Merge must never change the number of rows, even with duplicate join keys | `tests/test_evidence.py::test_build_evidence_matrix_row_count_matches_input_exactly` (regression test) + a runtime `assert` in `evidence.build_evidence_matrix` | Pass; see "Bugs found" below |
| Ranking-view row-count integrity | `combined_view`'s separate merge must also never change the row count, even when `hip_name` is shared by wide-binary components | `tests/test_ranking.py::test_combined_view_does_not_fan_out_on_shared_hip_name` (regression test) + a runtime `assert` in `ranking.combined_view` | Pass; see "Bugs found" below |
| Chi-squared-to-p-value conversion | Matches `scipy.stats.chi2.sf(chi2, df=2)` directly | `tests/test_evidence.py::test_hgca_significance_matches_chi2_survival_function` | Pass |
| Benjamini-Hochberg q-value calculation | Matches a hand-worked 4-star example exactly | `tests/test_evidence.py::test_bh_qvalues_hand_calculation` | Pass |
| Archive field-populated categories excluded from completeness | A star with only the two archive-bookkeeping fields present (no real coverage category) scores `evidence_completeness == 0.0` | `tests/test_evidence.py::test_archive_flag_populated_categories_excluded_from_completeness` (regression test) | Pass |
| Accelerator-detection logic | Flags only (significant acceleration) AND (no archive-listed planet); does not flag either condition alone | `tests/test_conflicts.py` (4 cases) | Pass |
| Ranking views stay separate | `combined_view` never produces a merged score column; a synthetic "high value, low evidence" star ranks #1 by value and worst by evidence simultaneously | `tests/test_ranking.py::test_combined_view_keeps_two_separate_rank_columns_not_merged` | Pass |

## Bugs found and fixed

**Before initial publication (2026-08-28)**: running the full pipeline
against live data (not just the test suite) surfaced a real bug:
`DI_STARS_EXEP` contains five wide binary systems whose two components
share one Hipparcos number (e.g. Xi Boo A/B, both `HIP 72659`). The first
version of `load_hgca_for_hip` queried VizieR once per *row* rather than
once per *unique* HIP number, producing a duplicated HGCA row for each
such pair; the subsequent merge in `build_evidence_matrix` then fanned out
(2 star rows x 2 duplicate HGCA rows = 4 output rows instead of 2),
silently inflating the evidence matrix from 164 to 172 rows. Fixed by
deduplicating the HIP query list in `cli.py` and adding a defensive
`drop_duplicates` plus a runtime row-count `assert` in
`evidence.build_evidence_matrix`, with a regression test reproducing the
exact scenario
(`tests/test_evidence.py::test_build_evidence_matrix_row_count_matches_input_exactly`).

**Found by external review, fixed 2026-08-29**: that first fix protected
`build_evidence_matrix`'s own internal HGCA join, but `ranking.py`'s
`combined_view` performs a *separate* merge of `stars` against `evidence`
on `hip_name` -- which is not a unique key for the same five wide-binary
pairs -- and was not protected. This inflated `results/ranking.csv` from
164 to 174 rows (some targets appearing up to 4 times). Fixed by
introducing a stable `target_id`, assigned once at load time in
`data.py`, threaded through every downstream table, and used for every
merge instead of `hip_name`/`hip_number`; added a row-count assertion and
a regression test
(`tests/test_ranking.py::test_combined_view_does_not_fan_out_on_shared_hip_name`).
The same review found that `evidence_completeness` included two archive
fields populated for essentially every row regardless of real coverage
(`sy_planets_flag`/`sy_disks_flag` populated); fixed by excluding them
from the score (see `COVERAGE_CATEGORIES` in `evidence.py`) and adding a
regression test
(`test_archive_flag_populated_categories_excluded_from_completeness`). See
`docs/CLAIMS.md` "Superseded / corrected claims" and `CHANGELOG.md` for
the full account.

## Explicitly not yet validated

- No independent cross-check of the chi-squared-to-acceleration-detection
  interpretation against a second HGCA-based companion-detection study.
- No manual literature check, star by star, of the 31 (28 FDR-corrected)
  flagged HGCA accelerators without an archive-listed planet -- they are
  reported as candidates for follow-up, not individually verified against
  the literature in this version.

## Reproducing these checks

```bash
pytest -q               # fixture-based, no network, < 5 s
pytest -q -m network      # + 2 live-service checks
```
