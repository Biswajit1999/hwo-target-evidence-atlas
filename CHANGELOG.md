# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-09-01

- Reframe the display title as a candidate-target catalog cross-match.
- Add a reproducible per-category coverage table with Wilson 95% intervals.
- State explicitly that 90.9% is catalog-field availability, not mission
  readiness, official target completeness, or imaging detectability.
- Eliminate a pandas nullable-boolean conversion warning.

## [0.2.0] - 2026-08-29

An external review (Codex) of this repository found one critical bug and
several overstated interpretations. All are fixed in this release; none
required withholding a result, but the ranking output and the completeness
definition both changed and every affected result file has been
regenerated from a fresh live run -- see `docs/CLAIMS.md` "Superseded /
corrected claims" for the full before/after account.

### Fixed

- **Critical**: `ranking.py`'s `combined_view` merged `stars` and
  `evidence` on `hip_name`, which is not a unique row key (5 wide-binary
  pairs share one Hipparcos number and hip_name string), inflating
  `results/ranking.csv` from 164 to 174 rows with some targets appearing
  up to 4 times. Fixed by assigning a stable `target_id` once at load time
  (`data.py`) and threading it through every downstream table and merge;
  added a row-count assertion and a regression test
  (`tests/test_ranking.py::test_combined_view_does_not_fan_out_on_shared_hip_name`).
- **High**: `evidence_completeness` previously averaged in two categories
  (`known_companions`, `exozodiacal_dust` -- renamed
  `archive_planet_flag_populated`, `archive_disk_flag_populated`) that are
  populated for essentially every target regardless of whether any real
  companion or exozodi observation was performed, silently inflating every
  star's score. Now excluded from the score (`COVERAGE_CATEGORIES` vs.
  `EVIDENCE_CATEGORIES` in `evidence.py`); mean completeness across the
  four real coverage categories is 90.9% (previously reported as a
  6-category average that included the two always-populated fields).
- **High**: `find_undisclosed_companion_conflicts` (renamed
  `find_hgca_accelerators_without_archive_listed_planets`) implied the two
  catalogs "disagree" when `sy_planets_flag == "N"` and a significant HGCA
  acceleration coincide. `sy_planets_flag == "N"` means no archive-listed
  planet, not a confirmed single-star determination, so this is not an
  established conflict -- language corrected throughout, and a
  Benjamini-Hochberg FDR correction is now also reported
  (`hgca_accel_qvalue`, `hgca_significant_accel_fdr`) since the raw p<0.01
  threshold is applied across 164 simultaneous comparisons (31 accelerators
  without a listed planet at raw significance, 28 after FDR correction).
- **Medium**: `ranking.py`'s `science_value_rank` column renamed to
  `distance_rank` -- it is a single distance proxy, not a composite
  scientific-value score (see `docs/METHODS.md`).
- **Medium**: `_parse_hgca_votable_row` used a fixed-column-order regex
  over the raw VOTable XML, which would silently misassign or drop data on
  a VizieR-side reordering or schema change. Rewritten using
  `defusedxml.ElementTree` with columns matched by their own `<FIELD
  name=...>` declarations; raises instead of silently returning `None` on
  any structural mismatch other than the expected empty-result case.
- **Low**: `docs/DATA_SOURCES.md`'s HGCA URL had a non-runnable `&...`
  placeholder; replaced with the exact, runnable query template and a
  live example URL.
- **Low**: an `== False` comparison in `tests/test_evidence.py` (ruff
  E712, not caught by this project's default lint rule selection) rewritten
  as `not ...`.

### Changed

- `matplotlib` (previously an unused declared dependency) is now used by a
  new, committed `scripts/make_figures.py` that regenerates
  `results/figures/evidence_completeness.png` from `results/*.csv`,
  visually distinguishing real coverage categories from the excluded
  archive-bookkeeping fields.
- `results/conflicts.csv` renamed to
  `results/hgca_accelerators_without_listed_planets.csv` to match the
  renamed, more accurate framing.

## [0.1.0] - 2026-08-28

### Added

- Live adapter for the NASA Exoplanet Archive `DI_STARS_EXEP` table (the
  164-star Mamajek & Stapelfeldt 2024 Direct Imaging ExEP Mission Star
  List), with checksum-manifested caching (`src/hwoevidence/data.py`).
- Live cross-match against the Hipparcos-Gaia Catalog of Accelerations
  (HGCA, Brandt 2021) via VizieR.
- A six-category evidence-completeness matrix (stellar parameters,
  activity, multiplicity, known companions, exozodiacal dust, astrometric
  acceleration), with an explicit distinction between "no measurement
  attempted" and "measured, and the answer was no"
  (`src/hwoevidence/evidence.py`).
- Conflict detection between catalogs: stars with a statistically
  significant HGCA acceleration but no known companion in the NASA
  Exoplanet Archive list (`src/hwoevidence/conflicts.py`).
- Two deliberately separate ranking views (scientific value by distance;
  evidence completeness) that are never merged into one score
  (`src/hwoevidence/ranking.py`).
- CLI (`hwoevidence build`) and test suite (18 fast tests using real,
  small catalog excerpts; 2 live network tests).
- One real bug caught and fixed by running the pipeline against live data
  before publishing: a wide-binary star sharing one Hipparcos number
  across two catalog rows fanned out the merge in
  `build_evidence_matrix`, inflating the output from 164 to 172 rows; now
  deduplicated with a regression test and a defensive assertion
  (`docs/VALIDATION.md`).

### Results

- Evidence completeness across the 164 targets (`results/`, generated by
  `hwoevidence build`): stellar parameters 100%, activity 99.4%,
  multiplicity (WDS cross-match) 66.5%, known-companion flag 100%,
  exozodiacal-dust flag 100%, HGCA astrometric-acceleration entry 97.6%.
- 31 candidate "undisclosed companion" conflicts: targets with a
  statistically significant (p < 0.01) HGCA acceleration but no known
  companion flagged in the NASA Exoplanet Archive list.
