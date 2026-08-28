"""Offline tests use small, real excerpts of both live catalogs (copied
verbatim from the NASA Exoplanet Archive TAP JSON response and a VizieR
HGCA VOTABLE response, both fetched 2026-08-28) so the parsers are checked
without a network dependency. Network-marked tests exercise the live
services directly.
"""
import json

import pandas as pd
import pytest

from hwoevidence.data import CachePaths, _extract_hip_number, _parse_hgca_votable_row

# Two real rows from DI_STARS_EXEP (NASA Exoplanet Archive TAP JSON), fields
# trimmed to what this project uses.
_DI_STARS_EXCERPT = [
    {"hip_name": "HIP 41926", "hd_name": "HD 72673", "hip_compname": None,
     "sy_dist": 12.1643, "sy_planets_flag": "N", "sy_disks_flag": "N",
     "st_teff": 5261, "st_mass": 0.85, "st_rad": 0.765, "st_logg": 4.560,
     "st_log_rhk": -4.946, "wds_designation": None},
    {"hip_name": "HIP 43587", "hd_name": "HD 75732 A", "hip_compname": "A",
     "sy_dist": 12.59, "sy_planets_flag": "Y", "sy_disks_flag": "N",
     "st_teff": 5172, "st_mass": 0.905, "st_rad": 0.943, "st_logg": 4.44,
     "st_log_rhk": -4.991, "wds_designation": "08181+2810"},
]

# A real per-star VizieR HGCA VOTABLE fragment for HIP 41926 (trimmed to the
# <TR> row used by _parse_hgca_votable_row).
_HGCA_VOTABLE_EXCERPT = """<TABLEDATA>
<TR><TD>41926</TD><TD>5640565607657897728</TD><TD>128.208756</TD><TD>-31.497487</TD><TD>82.2080</TD><TD>0.0178</TD><TD>-1113.739</TD><TD>762.420</TD><TD>0.018</TD><TD>0.028</TD><TD>4.444e-01</TD></TR>
</TABLEDATA>"""


def test_extract_hip_number():
    assert _extract_hip_number("HIP 41926") == 41926
    assert _extract_hip_number("HIP  43587") == 43587
    assert _extract_hip_number(None) is None
    assert _extract_hip_number("not a hip name") is None


def test_di_stars_excerpt_has_expected_real_values():
    df = pd.DataFrame(_DI_STARS_EXCERPT)
    df["hip_number"] = df["hip_name"].apply(_extract_hip_number)
    row = df[df["hd_name"] == "HD 75732 A"].iloc[0]  # 55 Cancri A
    assert row["sy_planets_flag"] == "Y"  # 55 Cnc is a well-known multi-planet system
    assert row["hip_number"] == 43587


def test_parse_hgca_votable_row_real_fragment():
    row = _parse_hgca_votable_row(_HGCA_VOTABLE_EXCERPT, hip=41926)
    assert row["HIP"] == 41926
    assert row["Gaia"] == 5640565607657897728
    assert row["chi2"] == pytest.approx(0.4444)
    assert row["pmRA"] == pytest.approx(-1113.739)


def test_parse_hgca_votable_row_no_match_returns_none():
    assert _parse_hgca_votable_row("<TABLEDATA></TABLEDATA>", hip=1) is None


@pytest.mark.network
def test_live_di_stars_exep_has_164_rows(tmp_path):
    from hwoevidence.data import load_di_stars_exep

    paths = CachePaths(cache_dir=tmp_path)
    df = load_di_stars_exep(paths)
    assert len(df) == 164
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert "di_stars_exep.json" in manifest


@pytest.mark.network
def test_live_hgca_cross_match(tmp_path):
    from hwoevidence.data import load_hgca_for_hip

    paths = CachePaths(cache_dir=tmp_path)
    df = load_hgca_for_hip([41926], paths)
    assert len(df) == 1
    assert df.iloc[0]["HIP"] == 41926
