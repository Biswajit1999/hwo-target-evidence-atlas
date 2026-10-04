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
import xml.etree.ElementTree as ET  # type hints only; parsing uses defusedxml below
from dataclasses import dataclass
from pathlib import Path

import defusedxml.ElementTree as DefusedET
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


def _verify_cached_file(name: str, data: bytes, paths: CachePaths) -> None:
    """Fail closed when a cached source snapshot does not match its manifest."""
    if not paths.manifest.exists():
        raise ValueError(f"cached source {name} has no checksum manifest")
    manifest = json.loads(paths.manifest.read_text())
    if name not in manifest:
        raise ValueError(f"cached source {name} has no checksum entry")
    observed = hashlib.sha256(data).hexdigest()
    expected = manifest[name].get("sha256")
    if observed != expected:
        raise ValueError(f"cached source {name} checksum mismatch: {observed} != {expected}")


def load_di_stars_exep(paths: CachePaths, force: bool = False) -> pd.DataFrame:
    """Fetch (or read cached) the 164-row Direct Imaging ExEP Mission Star
    List from the NASA Exoplanet Archive TAP service."""
    cache_file = paths.cache_dir / "di_stars_exep.json"
    if cache_file.exists() and not force:
        raw = cache_file.read_bytes()
        _verify_cached_file(cache_file.name, raw, paths)
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
    # Row order is not an identity: TAP services may legally reorder rows.
    # Build a deterministic composite identifier from catalogue names and the
    # component label, then fail closed if upstream identity fields no longer
    # distinguish all targets.
    df["target_id"] = df.apply(_stable_target_id, axis=1)
    if not df["target_id"].is_unique:
        duplicates = df.loc[df["target_id"].duplicated(False), "target_id"].tolist()
        raise ValueError(f"DI_STARS_EXEP target identity collision: {duplicates}")
    return df


def _stable_target_id(row: pd.Series) -> str:
    fields = ("hostname", "hip_name", "hip_compname", "hd_name", "tic_id")
    values = []
    for field in fields:
        value = row.get(field)
        values.append("" if pd.isna(value) else str(value).strip().casefold())
    identity = "|".join(values)
    if not identity.replace("|", ""):
        raise ValueError("DI_STARS_EXEP row has no usable catalogue identity")
    return "hwo-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


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
        raw = cache_file.read_bytes()
        _verify_cached_file(cache_file.name, raw, paths)
        rows = json.loads(raw)
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


def _local_tag(elem: ET.Element) -> str:
    """Element tag without its XML namespace prefix (VOTable responses use
    a versioned default namespace, e.g. '{http://www.ivoa.net/xml/VOTable/v1.3}FIELD')."""
    tag = elem.tag
    return tag.split("}", 1)[1] if "}" in tag else tag


def _parse_hgca_votable_row(xml_text: str, hip: int) -> dict | None:
    """Extract the single data row from a small per-star HGCA VOTABLE
    response using real XML parsing (``xml.etree.ElementTree``), not a
    fixed-column-order regex.

    Column names are read from the response's own ``<FIELD name=...>``
    elements, in the order VizieR actually returned them, and matched by
    name against the requested ``HGCA_COLUMNS`` -- so a VizieR-side
    reordering or the addition/removal of a column does not silently
    misassign values to the wrong field. Returns ``None`` (with the
    specific reason distinguishable via the raised exception during
    development/debugging) only for the expected "no match for this HIP"
    case of an empty result table; any other structural surprise (a
    genuinely malformed or unexpectedly-shaped response) raises rather
    than silently returning a wrong or missing row.
    """
    root = DefusedET.fromstring(xml_text)
    fields = [
        el.attrib["name"]
        for el in root.iter()
        if _local_tag(el) == "FIELD" and "name" in el.attrib
    ]
    if not fields:
        raise ValueError(f"HGCA VOTable response for HIP {hip} has no FIELD definitions")

    trs = [el for el in root.iter() if _local_tag(el) == "TR"]
    if not trs:
        return None  # expected case: no HGCA cross-match for this HIP

    tds = [el for el in trs[0] if _local_tag(el) == "TD"]
    if len(tds) != len(fields):
        raise ValueError(
            f"HGCA VOTable response for HIP {hip}: {len(fields)} FIELDs but "
            f"{len(tds)} TD cells in the data row -- response shape does not "
            f"match its own schema"
        )

    raw = {name: (td.text or "").strip() for name, td in zip(fields, tds)}
    missing = [c for c in HGCA_COLUMNS if c not in raw]
    if missing:
        raise ValueError(
            f"HGCA VOTable response for HIP {hip} is missing expected column(s) "
            f"{missing} -- upstream schema may have changed (see docs/DATA_SOURCES.md)"
        )

    row = {}
    for name in HGCA_COLUMNS:
        val = raw[name]
        if val == "":
            row[name] = None
        elif name in ("HIP", "Gaia"):
            row[name] = int(val)
        else:
            row[name] = float(val)
    return row
