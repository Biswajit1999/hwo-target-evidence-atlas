# Methods

## Research question

Which candidate Habitable Worlds Observatory (HWO) direct-imaging targets
have complete real observational coverage -- stellar parameters,
multiplicity, activity, and astrometric acceleration -- and for which
stars is a significant HGCA astrometric acceleration not matched by an
archive-listed planet?

## Null hypothesis

H0: Observational-coverage completeness is uniform across the 164-target
list (no systematic gaps by category), and every star with a
statistically significant HGCA astrometric acceleration also has an
archive-listed planet.

This is not expected to hold, and does not: multiplicity evidence
(Washington Double Star cross-match) is present for only 66.5% of targets,
and 31 targets (28 after Benjamini-Hochberg FDR correction) show a
statistically significant astrometric acceleration with no archive-listed
planet (`results/hgca_accelerators_without_listed_planets.csv`,
`docs/VALIDATION.md`). Quantifying and cataloging that gap, not merely
asserting it exists, is this project's contribution.

## Why evidence completeness and scientific value are never merged

A single blended "target readiness score" would hide the one distinction
that matters for HWO pre-launch characterization planning: a
scientifically excellent, nearby, high-contrast target with *no* activity
or multiplicity measurement looks identical to a mediocre but
well-characterized one under a merged number. `src/hwoevidence/ranking.py`
therefore always returns evidence completeness and scientific value (here,
proxied simply by distance) as two separate ranked columns, explicitly
tested to never collapse into one (`tests/test_ranking.py`).

## Evidence categories

Six categories are scored per star (`src/hwoevidence/evidence.py`), each
recording *whether a measurement exists*, not whether the star is
favorable -- but only four of them (`COVERAGE_CATEGORIES`) feed into
`evidence_completeness`; the other two are tracked but deliberately
excluded (see below):

1. **Stellar parameters** (coverage): Teff, mass, radius, and logg all measured.
2. **Activity** (coverage): chromospheric activity index log(R'HK) measured.
3. **Multiplicity** (coverage): a Washington Double Star catalog cross-match
   record exists. Absence means "no WDS entry found," not "confirmed single
   star" -- WDS is a visual-binary catalog and cannot rule out close,
   non-resolved, or non-astrometric companions. This distinction is
   enforced in code (the category function checks for record presence,
   never infers "single") and tested
   (`tests/test_evidence.py::test_multiplicity_present_only_with_wds_entry`).
4. **Astrometric acceleration** (coverage): the star has an HGCA entry at
   all (a separate, non-gating field, `hgca_significant_accel` /
   `hgca_significant_accel_fdr`, records whether that acceleration is
   statistically significant, raw and FDR-corrected respectively).
5. **Archive planet-flag populated** (NOT coverage): the archive's
   `sy_planets_flag` is populated. This is essentially always true for
   this target list regardless of whether a companion search was ever
   performed, so it is excluded from `evidence_completeness` -- see
   `docs/LIMITATIONS.md`.
6. **Archive disk-flag populated** (NOT coverage): the archive's
   `sy_disks_flag` is populated. Same caveat and exclusion as above; see
   `docs/LIMITATIONS.md` for why this is not evidence of a dedicated
   exozodi survey.

`evidence_completeness` is the fraction of the four *coverage* categories
present for a given star (0 to 1), reported alongside all six per-category
booleans -- never collapsed further into a single opaque score, and never
inflated by the two always-populated archive-bookkeeping fields.

## Conflict detection

`src/hwoevidence/conflicts.py::find_hgca_accelerators_without_archive_listed_planets`
flags stars with p < 0.01 (HGCA acceleration chi-squared, 2 degrees of
freedom, Brandt 2021) but `sy_planets_flag == "N"`, and separately reports
the same comparison at Benjamini-Hochberg FDR-corrected significance
(`hgca_significant_accel_fdr`) to account for testing 164 stars
simultaneously. This is explicitly not framed as a catalog "conflict":
`sy_planets_flag == "N"` means no archive-listed planet, not a confirmed
single-star determination, so the two catalogs are not necessarily in
disagreement -- the acceleration may come from a stellar, brown-dwarf, or
planetary-mass companion the archive simply hasn't listed as a planet. An
astrometric acceleration establishes that a stationary-point-mass model is
statistically disfavored, not the companion's mass, period, or nature.

## What this project does not do

- No claim that any specific star does or does not have a planet, a
  companion, or exozodiacal dust beyond what the cited catalogs directly
  state.
- No single composite "readiness score" -- by design (see above).
- No claim about which targets HWO will actually observe; target selection
  is a mission-level decision this project has no role in.
