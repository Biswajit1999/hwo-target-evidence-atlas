"""hwoevidence: an evidence-completeness cross-match for Habitable Worlds
Observatory (HWO) candidate direct-imaging targets.

Combines the NASA Exoplanet Archive's Direct Imaging ExEP Mission Star List
(the 164-target catalog of Mamajek & Stapelfeldt 2024) with the
Hipparcos-Gaia Catalog of Accelerations (Brandt 2021, via VizieR) to report,
per star and per evidence category, whether a given catalog field is
populated at all (see ``COVERAGE_CATEGORIES`` vs. ``EVIDENCE_CATEGORIES``
in ``evidence.py`` for exactly which fields count as real observational
coverage), and which stars have a significant HGCA astrometric
acceleration with no archive-listed planet -- a candidate for follow-up,
not an established conflict between the two catalogs (see
``conflicts.py``).

This package makes no claim about which targets HWO will observe, does not
establish that any given evidence category reflects an actual completed
observation vs. a merely-populated archive field, and does not assign a
single combined "readiness score" -- see docs/METHODS.md and
docs/LIMITATIONS.md for why evidence completeness and scientific priority
are kept as separate, never-merged outputs, and for exactly what each
evidence category does and does not establish.
"""

__version__ = "0.3.0"
