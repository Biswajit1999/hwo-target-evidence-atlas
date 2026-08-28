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

## Exozodiacal dust proxy

- The `exozodiacal_dust` category uses the archive's `sy_disks_flag`,
  which is populated for all 164 targets (100% "evidence present" by this
  project's definition) but conflates several different underlying
  situations: a dedicated interferometric null (e.g. from the HOSTS
  survey, which has directly observed only ~23 of the 164 targets), an
  infrared-excess-based disk detection/non-detection, or simply an
  absence of any reported excess in whatever compilation the archive used.
  A 100%-complete flag column is not the same claim as "164/164 targets
  have a dedicated exozodi observation" -- the latter is false (only ~23
  do, per the HOSTS survey found during research). Do not read this
  project's 100% exozodi-evidence number as survey coverage.

## Astrometric acceleration

- HGCA cross-match failed for a small number of targets (see
  `docs/DATA_SOURCES.md` for the exact count) -- likely fast-proper-motion
  or otherwise problematic Hipparcos/Gaia cross-matches for those specific
  stars, not investigated further in this version.
- A significant HGCA acceleration (`docs/METHODS.md`) is evidence of *some*
  unmodeled companion, not a detection of a specific companion's mass,
  period, or nature. The 31 flagged "undisclosed companion" conflicts
  (`results/conflicts.csv`) are candidates for follow-up, not confirmed
  discoveries -- and this project makes no claim to have discovered
  anything.
- The chi-squared significance threshold (p < 0.01, `ACCEL_SIGNIFICANCE_ALPHA`
  in `src/hwoevidence/evidence.py`) is a documented, arbitrary choice, not
  a value derived from or validated against this specific target
  population's false-positive characteristics.

## What is not yet integrated

See `docs/DATA_SOURCES.md` "Explicitly not used" for real, citable sources
(archival UV/X-ray data, SPORES-HWO RV companion-mass limits, the larger
HPIC catalog) found during research but not yet cross-matched -- tracked
as repository issues rather than silently left out of scope.

## No population statistics beyond this specific list

This project reports evidence completeness for exactly the 164 targets in
`DI_STARS_EXEP`. It makes no claim about evidence completeness for HWO
targets in general, or for any target not on that specific list.
