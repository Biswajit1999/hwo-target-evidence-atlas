"""hwoevidence: an evidence-completeness cross-match for Habitable Worlds
Observatory (HWO) candidate direct-imaging targets.

Combines the NASA Exoplanet Archive's Direct Imaging ExEP Mission Star List
(the 164-target catalog of Mamajek & Stapelfeldt 2024) with the
Hipparcos-Gaia Catalog of Accelerations (Brandt 2021, via VizieR) to report,
per star and per evidence category, whether the measurement needed to judge
observing readiness exists at all, and where the two catalogs' evidence is
in tension (e.g. a significant astrometric acceleration with no catalogued
companion).

This package makes no claim about which targets HWO will observe, and does
not assign a single combined "readiness score" -- see docs/METHODS.md for
why evidence completeness and scientific priority are kept as separate,
never-merged outputs.
"""

__version__ = "0.1.0"
