# Data Sources

## NASA Exoplanet Archive: `DI_STARS_EXEP`

- **Provider**: NASA Exoplanet Archive (NASA Exoplanet Science Institute,
  Caltech/IPAC), TAP synchronous endpoint.
- **URL**: `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+DI_STARS_EXEP&format=json`
- **Underlying publication**: Mamajek, E. E. & Stapelfeldt, K. R. (2024),
  "Setting the Stage for the Search for Life with the Habitable Worlds
  Observatory: Properties of 164 Promising Planet-survey Targets," ApJS
  272, 32. Archive DOI: 10.26133/NEA39.
- **Accessed**: 2026-10-04. Row count confirmed 164 (matches the paper's
  target-list size exactly; see `docs/VALIDATION.md`).
- **Licence**: NASA Exoplanet Archive data are public domain (U.S.
  Government work); the archive requests citation of the underlying
  publication, included above and in `CITATION.cff`.
- **Fields used**: stellar identifiers (HIP/HD/TIC), coordinates, distance,
  stellar parameters (Teff, mass, radius, logg, metallicity) with
  per-field reference links, chromospheric activity index (log R'HK),
  Washington Double Star (WDS) cross-match fields, known-planet and
  circumstellar-disk flags, and predicted Earth-twin RV/astrometric signal
  amplitudes. The full 58-column schema is documented by the archive
  itself; this project uses a documented subset
  (`src/hwoevidence/evidence.py`).

## Hipparcos-Gaia Catalog of Accelerations (HGCA), Gaia EDR3 edition

- **Provider**: VizieR (Centre de Données astronomiques de Strasbourg),
  catalog `J/ApJS/254/42`.
- **URL**: `https://vizier.cds.unistra.fr/viz-bin/votable?-source=J/ApJS/254/42&-out.max=5&-out=HIP,Gaia,RA_ICRS,DE_ICRS,plx,e_plx,pmRA,pmDE,e_pmRA,e_pmDE,chi2&HIP=<hip_number>`
  (one query per Hipparcos number, `<hip_number>` substituted per star; see
  `VIZIER_HGCA_URL`/`HGCA_CATALOG`/`HGCA_COLUMNS` in `src/hwoevidence/data.py`
  for the exact, runnable construction -- e.g. for HIP 72659:
  <https://vizier.cds.unistra.fr/viz-bin/votable?-source=J/ApJS/254/42&-out.max=5&-out=HIP,Gaia,RA_ICRS,DE_ICRS,plx,e_plx,pmRA,pmDE,e_pmRA,e_pmDE,chi2&HIP=72659>).
- **Underlying publication**: Brandt, T. D. (2021), "The Hipparcos-Gaia
  Catalog of Accelerations: Gaia EDR3 Edition," ApJS 254, 42.
- **Accessed**: 2026-10-04. 160/164 (156/159 unique Hipparcos numbers
  after deduplicating shared-HIP binary components; see
  `docs/VALIDATION.md`) targets successfully cross-matched.
- **Licence**: VizieR/CDS data are freely usable for research with
  attribution to the original publication (CDS licence terms:
  <https://cds.unistra.fr/vizier-org/licences_vizier.html>).
- **Field used**: `chi2`, the chi-squared statistic (2 degrees of freedom)
  for a constant-proper-motion model, converted to a p-value via
  `scipy.stats.chi2.sf` (`src/hwoevidence/evidence.py`). A low p-value
  means the star's motion is inconsistent with a single, stationary point
  mass -- i.e. evidence of an unresolved companion.

## Explicitly not used in this v0.1

Several real, citable HWO-related catalogs found during research (see
`docs/METHODS.md`) are documented here as known, not-yet-integrated
extensions rather than silently omitted:

- HPIC (Habitable Worlds Observatory Preliminary Input Catalog; Tuomi et
  al. 2024, AJ 167, 139) -- a much larger (~13,000-star) catalog; this
  project deliberately starts from the smaller, community-vetted 164-target
  list to keep the evidence matrix's target set unambiguous and matched to
  a specific, citable priority tier.
- HOSTS exozodiacal-dust survey (Ertel et al.) -- partial coverage
  (~23/164 targets observed); `sy_disks_flag` in `DI_STARS_EXEP` is used
  instead as a documented proxy, which conflates "assessed and found
  clear" with "not part of any dedicated exozodi survey" -- see
  `docs/LIMITATIONS.md`.
- Archival UV/X-ray survey (a 2025 paper found during research) -- a real,
  directly relevant source for the "high-energy radiation" evidence axis
  named in the programme's original research question; not yet integrated
  (tracked as a repository issue).
- SPORES-HWO II (RV companion-mass limits from 35 yr of Doppler
  monitoring) -- would sharpen the "known companions" category beyond the
  current binary Y/N flag; not yet integrated (tracked as a repository
  issue).

The v0.3 release also preserves the exact 2026-10-04 source snapshots in
`data/cache/`, together with SHA-256 digests and request provenance in
`data/cache/manifest.json`. The adapters can still refresh both public
sources directly; the committed snapshot makes the published tables
reconstructible if an upstream catalogue later changes.
