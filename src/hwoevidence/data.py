"""Adapters for the two public catalogs this project cross-matches.

1. NASA Exoplanet Archive, table ``DI_STARS_EXEP``: the Direct Imaging ExEP
   Mission Star List, i.e. the 164 stars of Mamajek & Stapelfeldt (2024),
   "Setting the Stage for the Search for Life with the Habitable Worlds
   Observatory," ApJS 272, 32 (NASA Exoplanet Archive DOI 10.26133/NEA39).
   Queried live via the archive's TAP synchronous endpoint (ADQL).
2. Hipparcos-Gaia Catalog of Accelerations (HGCA), Gaia EDR3 edition
   (Brandt 2021, ApJS 254, 42), queried live via VizieR (catalog
   J/ApJS/254/42), cross-matched by Hipparcos identifier.

Both are fetched on demand into a local, git-ignored cache with a SHA-256
checksum manifest -- see docs/DATA_SOURCES.md for full provenance.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

NEA_TAP_SYNC = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
DI_STARS_EXEP_QUERY = "select * from DI_STARS_EXEP"

VIZIER_HGCA_URL = "https://vizier.cds.unistra.fr/viz-bin/votable"
HGCA_CATALOG = "J/ApJS/254/42"
HGCA_COLUMNS = [
    "HIP", "Gaia", "RA_ICRS", "DE_ICRS", "plx", "e_plx",
    "pmRA", "pmDE", "e_pmRA", "e_pmDE", "chi2",
]


@dataclass(frozen=True)
class CachePaths:
    cache_dir: Path

    @property
    def manifest(self) -> Path:
        return self.cache_dir / "manifest.json"


def _record_manifest(name: str, url: str, data: bytes, paths: CachePaths) -> None:
    paths.cache_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "url": url,
        "sha256": hashlib.sha256(data).hexdigest(),
        "n_bytes": len(data),
        "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest = {}
    if paths.manifest.exists():
        manifest = json.loads(paths.manifest.read_text())
    manifest[name] = entry
    paths.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def load_di_stars_exep(paths: CachePaths, force: bool = False) -> pd.DataFrame:
    """Fetch (or read cached) the 164-row Direct Imaging ExEP Mission Star
    List from the NASA Exoplanet Archive TAP service."""
    cache_file = paths.cache_dir / "di_stars_exep.json"
    if cache_file.exists() and not force:
        raw = cache_file.read_bytes()
    else:
        url = NEA_TAP_SYNC + "?" + urllib.parse.urlencode(
            {"query": DI_STARS_EXEP_QUERY, "format": "json"}
        )
        with urllib.request.urlopen(url, timeout=60) as resp:
            raw = resp.read()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(raw)
        _record_manifest("di_stars_exep.json", url, raw, paths)

    records = json.loads(raw)
    df = pd.DataFrame(records)
    df["hip_number"] = df["hip_name"].apply(_extract_hip_number)
    return df


def _extract_hip_number(hip_name: object) -> int | None:
    if not isinstance(hip_name, str):
        return None
    m = re.search(r"HIP\s*(\d+)", hip_name)
    return int(m.group(1)) if m else None


def load_hgca_for_hip(hip_numbers: list[int], paths: CachePaths, force: bool = False) -> pd.DataFrame:
    """Cross-match a list of Hipparcos numbers against the HGCA via VizieR.

    Queries one HIP number at a time (VizieR's simple ASU interface does not
    take a list filter cleanly for this catalog); results are cached
    per-batch keyed by the sorted HIP list so repeated runs over the same
    target list do not re-query the network.
    """
    cache_key = "hgca_" + hashlib.sha256(
        ",".join(str(h) for h in sorted(hip_numbers)).encode()
    ).hexdigest()[:16] + ".json"
    cache_file = paths.cache_dir / cache_key
    if cache_file.exists() and not force:
        rows = json.loads(cache_file.read_text())
        return pd.DataFrame(rows)

    rows = []
    for hip in hip_numbers:
        url = VIZIER_HGCA_URL + "?" + urllib.parse.urlencode(
            {
                "-source": HGCA_CATALOG,
                "-out.max": "5",
                "-out": ",".join(HGCA_COLUMNS),
                "HIP": str(hip),
            }
        )
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml = resp.read().decode("utf-8", errors="replace")
        row = _parse_hgca_votable_row(xml, hip)
        if row is not None:
            rows.append(row)

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(rows, indent=2))
    _record_manifest(
        cache_key, VIZIER_HGCA_URL + " (per-HIP queries, see cached file)",
        cache_file.read_bytes(), paths,
    )
    return pd.DataFrame(rows)


def _parse_hgca_votable_row(xml_text: str, hip: int) -> dict | None:
    """Extract the single data row from a small per-star HGCA VOTABLE
    response without a full XML/VOTable dependency (only a handful of
    known, fixed-order numeric columns are needed)."""
    m = re.search(r"<TR>(.*?)</TR>", xml_text, re.DOTALL)
    if m is None:
        return None
    cells = re.findall(r"<TD>(.*?)</TD>", m.group(1))
    if len(cells) != len(HGCA_COLUMNS):
        return None
    row = {}
    for name, val in zip(HGCA_COLUMNS, cells):
        val = val.strip()
        if val == "":
            row[name] = None
        elif name in ("HIP", "Gaia"):
            row[name] = int(val)
        else:
            row[name] = float(val)
    return row
