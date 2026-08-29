# Limitations and Known Failure Modes

## Target list scope

- This project cross-matches the 164-star Mamajek & Stapelfeldt (2024)
  Direct Imaging ExEP Mission Star List, not the much larger (~13,000-star)
  HPIC preliminary input catalog, nor the newer TSS25 community list (both
  found during research; see `docs/DATA_SOURCES.md`). Results here should
  not be read as covering every plausible future HWO target.

## Multiplicity evidence

- "Multiplicity" evidence is scored purely from Washington Double Star
  (WDS) cross-match presence -- a visual-binary catalog. It cannot detect
  close spectroscopic binaries, non-resolved companions, or companions
  discovered only astrometrically (which is exactly what the separate
  `astrometric_acceleration` / conflict-detection category is for). A
  star flagged as having "no multiplicity evidence" may still have an
  unresolved companion; this is stated explicitly wherever the category is
  used, not just here.

## Archive field-populated categories are not observational coverage

- `archive_planet_flag_populated` (the archive's `sy_planets_flag`) and
  `archive_disk_flag_populated` (`sy_disks_flag`) are both populated for
  essentially all 164 targets, but a populated field only means the
  archive recorded *some* answer -- it does not mean any actual companion
  search or exozodi observation was performed. For the disk flag
  specifically: it conflates a dedicated interferometric null (e.g. from
  the HOSTS survey, which has directly observed only ~23 of the 164
  targets), an infrared-excess-based disk detection/non-detection, or
  simply an absence of any reported excess in whatever compilation the
  archive used. **Both categories are deliberately excluded from
  `evidence_completeness`** (see `NON_COVERAGE_CATEGORY_KEYS` in
  `src/hwoevidence/evidence.py`) for exactly this reason: including a
  field that is essentially always populated regardless of real survey
  coverage would silently inflate every star's completeness score by a
  fixed, uninformative amount. They are still reported as their own
  columns (so a real future gap in either field would still be visible),
  just never averaged into the headline completeness number. Do not read
  either category's near-100% populated rate as "100% of targets have a
  dedicated companion or exozodi observation" -- neither claim is true
  (e.g. only ~23/164 have a dedicated HOSTS exozodi observation, per the
  HOSTS survey found during research).

## Astrometric acceleration

- HGCA cross-match failed for a small number of targets (see
  `docs/DATA_SOURCES.md` for the exact count) -- likely fast-proper-motion
  or otherwise problematic Hipparcos/Gaia cross-matches for those specific
  stars, not investigated further in this version.
- A significant HGCA acceleration (`docs/METHODS.md`) is evidence of *some*
  unmodeled companion, not a detection of a specific companion's mass,
  period, or nature. `sy_planets_flag == "N"` means no archive-listed
  planet, not a confirmed single-star determination -- so the 31 stars in
  `results/hgca_accelerators_without_listed_planets.csv` are **not**
  established catalog conflicts, just candidates for follow-up. This
  project makes no claim to have discovered anything, and does not assert
  the two catalogs disagree.
- The chi-squared significance threshold (p < 0.01, `ACCEL_SIGNIFICANCE_ALPHA`
  in `src/hwoevidence/evidence.py`) is a documented, arbitrary choice, not
  a value derived from or validated against this specific target
  population's false-positive characteristics. Because this threshold is
  applied independently across 164 stars, a Benjamini-Hochberg FDR
  correction is also computed and reported (`hgca_accel_qvalue`,
  `hgca_significant_accel_fdr`): 40 stars are significant at raw p < 0.01,
  but only 35 survive FDR correction at the same nominal rate, and the
  "31 accelerators without a listed planet" headline count drops to 28
  under FDR correction -- report the FDR-corrected numbers when the
  multiple-comparisons context matters.

## What is not yet integrated

See `docs/DATA_SOURCES.md` "Explicitly not used" for real, citable sources
(archival UV/X-ray data, SPORES-HWO RV companion-mass limits, the larger
HPIC catalog) found during research but not yet cross-matched -- tracked
as repository issues rather than silently left out of scope.

## No population statistics beyond this specific list

This project reports evidence completeness for exactly the 164 targets in
`DI_STARS_EXEP`. It makes no claim about evidence completeness for HWO
targets in general, or for any target not on that specific list.
