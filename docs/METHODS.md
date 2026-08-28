# Methods

## Research question

Which candidate Habitable Worlds Observatory (HWO) direct-imaging targets
have sufficiently complete evidence for stellar parameters, multiplicity,
activity, high-energy radiation, RV companions, astrometric acceleration,
and exozodiacal contamination -- and where do independent catalogs
disagree about that evidence?

## Null hypothesis

H0: Evidence completeness is uniform across the 164-target list (no
systematic gaps by category), and the NASA Exoplanet Archive's
known-companion flag and the HGCA's astrometric-acceleration signal never
disagree.

This is not expected to hold, and does not: multiplicity evidence
(Washington Double Star cross-match) is present for only 66.5% of targets,
and 31 targets show a statistically significant astrometric acceleration
with no companion flagged in the archive's own list (`results/conflicts.csv`,
`docs/VALIDATION.md`). Quantifying and cataloging that disagreement, not
merely asserting it exists, is this project's contribution.

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
favorable:

1. **Stellar parameters**: Teff, mass, radius, and logg all measured.
2. **Activity**: chromospheric activity index log(R'HK) measured.
3. **Multiplicity**: a Washington Double Star catalog cross-match record
   exists. Absence means "no WDS entry found," not "confirmed single star"
   -- WDS is a visual-binary catalog and cannot rule out close,
   non-resolved, or non-astrometric companions. This distinction is
   enforced in code (the category function checks for record presence,
   never infers "single") and tested
   (`tests/test_evidence.py::test_multiplicity_present_only_with_wds_entry`).
4. **Known companions**: the archive's `sy_planets_flag` is populated.
5. **Exozodiacal dust**: the archive's `sy_disks_flag` is populated. See
   `docs/LIMITATIONS.md` for why this is an imperfect proxy for a
   dedicated exozodi survey.
6. **Astrometric acceleration**: the star has an HGCA entry at all (a
   separate, non-gating field, `hgca_significant_accel`, records whether
   that acceleration is statistically significant).

`evidence_completeness` is the simple fraction of these six categories
present for a given star (0 to 1), reported alongside the per-category
booleans -- never collapsed further into a single opaque score.

## Conflict detection

`src/hwoevidence/conflicts.py::find_undisclosed_companion_conflicts` flags
stars with p < 0.01 (HGCA acceleration chi-squared, 2 degrees of freedom,
Brandt 2021) but `sy_planets_flag == "N"`. This is framed explicitly as a
*candidate* conflict for follow-up, not a confirmed companion: an
astrometric acceleration establishes that a stationary-point-mass model is
statistically disfavored, not the companion's mass, period, or nature.

## What this project does not do

- No claim that any specific star does or does not have a planet, a
  companion, or exozodiacal dust beyond what the cited catalogs directly
  state.
- No single composite "readiness score" -- by design (see above).
- No claim about which targets HWO will actually observe; target selection
  is a mission-level decision this project has no role in.
