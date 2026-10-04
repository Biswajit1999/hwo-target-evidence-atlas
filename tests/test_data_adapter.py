"""Offline tests use small, real excerpts of both live catalogs (copied
verbatim from the NASA Exoplanet Archive TAP JSON response and a VizieR
HGCA VOTABLE response, both fetched 2026-08-28) so the parsers are checked
without a network dependency. Network-marked tests exercise the live
services directly.
"""
import json

import pandas as pd
import pytest

from hwoevidence.data import (
    CachePaths,
    _extract_hip_number,
    _parse_hgca_votable_row,
    _stable_target_id,
    _verify_cached_file,
)

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

# A real VizieR HGCA VOTABLE response for HIP 41926, re-fetched 2026-08-29
# (per-field <DESCRIPTION>/<LINK> tags trimmed for readability -- the parser
# doesn't read them -- but the namespace, FIELD name/order, and the TR/TD
# data row are exactly as returned by the live service).
_HGCA_VOTABLE_EXCERPT = """<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.4" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
<RESOURCE ID="yCat_22540042" name="J/ApJS/254/42" type="results">
  <TABLE ID="J_ApJS_254_42_catalog" name="J/ApJS/254/42/catalog">
    <FIELD name="HIP" datatype="int" width="6"/>
    <FIELD name="Gaia" datatype="long" width="19"/>
    <FIELD name="RA_ICRS" datatype="double" width="15" precision="11" unit="deg"/>
    <FIELD name="DE_ICRS" datatype="double" width="15" precision="11" unit="deg"/>
    <FIELD name="plx" datatype="double" width="8" precision="4" unit="mas"/>
    <FIELD name="e_plx" datatype="float" width="7" precision="4" unit="mas"/>
    <FIELD name="pmRA" datatype="double" width="9" precision="3" unit="mas/yr"/>
    <FIELD name="pmDE" datatype="double" width="9" precision="3" unit="mas/yr"/>
    <FIELD name="e_pmRA" datatype="float" width="6" precision="3" unit="mas/yr"/>
    <FIELD name="e_pmDE" datatype="float" width="6" precision="3" unit="mas/yr"/>
    <FIELD name="chi2" datatype="float" width="10" precision="E3"/>
<DATA><TABLEDATA>
<TR><TD>41926</TD><TD>5640565607657897728</TD><TD>128.20875554053</TD><TD>-31.49748704809</TD><TD>82.2080</TD><TD>0.0178</TD><TD>-1113.739</TD><TD>762.420</TD><TD>0.018</TD><TD>0.028</TD><TD>4.444e-01</TD></TR>
</TABLEDATA></DATA>
</TABLE>
<INFO name="matches" value="1">matching records</INFO>
</RESOURCE>
</VOTABLE>"""

# A real VizieR "no match" HGCA VOTABLE response (fetched 2026-08-29 for a
# deliberately out-of-range HIP number): FIELD definitions are present but
# there is no DATA/TABLEDATA section at all when nothing matches.
_HGCA_VOTABLE_NO_MATCH = """<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.4" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
<RESOURCE ID="yCat_22540042" name="J/ApJS/254/42" type="results">
  <TABLE ID="J_ApJS_254_42_catalog" name="J/ApJS/254/42/catalog">
    <FIELD name="HIP" datatype="int" width="6"/>
    <FIELD name="Gaia" datatype="long" width="19"/>
    <FIELD name="RA_ICRS" datatype="double" width="15" precision="11" unit="deg"/>
    <FIELD name="DE_ICRS" datatype="double" width="15" precision="11" unit="deg"/>
    <FIELD name="plx" datatype="double" width="8" precision="4" unit="mas"/>
    <FIELD name="e_plx" datatype="float" width="7" precision="4" unit="mas"/>
    <FIELD name="pmRA" datatype="double" width="9" precision="3" unit="mas/yr"/>
    <FIELD name="pmDE" datatype="double" width="9" precision="3" unit="mas/yr"/>
    <FIELD name="e_pmRA" datatype="float" width="6" precision="3" unit="mas/yr"/>
    <FIELD name="e_pmDE" datatype="float" width="6" precision="3" unit="mas/yr"/>
    <FIELD name="chi2" datatype="float" width="10" precision="E3"/>
<!--  EMPTY result, no DATA part  -->
</TABLE>
</RESOURCE>
</VOTABLE>"""


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


def test_target_identity_is_deterministic_and_null_safe():
    first = pd.Series(_DI_STARS_EXCERPT[0] | {"hostname": None, "tic_id": float("nan")})
    second = first.copy()
    assert _stable_target_id(first) == _stable_target_id(second)
    assert _stable_target_id(first).startswith("hwo-")


def test_component_label_distinguishes_shared_catalogue_names():
    base = {"hostname": None, "hip_name": "HIP 72659", "hd_name": "HD 131156", "tic_id": None}
    assert _stable_target_id(pd.Series(base | {"hip_compname": "A"})) != _stable_target_id(
        pd.Series(base | {"hip_compname": "B"})
    )


def test_cache_checksum_verification_fails_closed(tmp_path):
    cache = tmp_path / "source.json"
    cache.write_bytes(b"original")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source.json": {"sha256": "0682c5f2076f099c34cfdd15a9e063849ed437a49677e6fcc5b4198c76575be5"}
    }))
    paths = CachePaths(cache_dir=tmp_path)
    _verify_cached_file("source.json", b"original", paths)
    with pytest.raises(ValueError, match="checksum mismatch"):
        _verify_cached_file("source.json", b"modified", paths)


def test_parse_hgca_votable_row_real_fragment():
    row = _parse_hgca_votable_row(_HGCA_VOTABLE_EXCERPT, hip=41926)
    assert row["HIP"] == 41926
    assert row["Gaia"] == 5640565607657897728
    assert row["chi2"] == pytest.approx(0.4444)
    assert row["pmRA"] == pytest.approx(-1113.739)


def test_parse_hgca_votable_row_no_match_returns_none():
    assert _parse_hgca_votable_row(_HGCA_VOTABLE_NO_MATCH, hip=999999999) is None


def test_parse_hgca_votable_row_raises_on_missing_field_definitions():
    """A response with no FIELD elements at all is a structural surprise,
    not the expected 'no match' case, and should raise rather than
    silently return None (see _parse_hgca_votable_row docstring)."""
    with pytest.raises(ValueError, match="no FIELD definitions"):
        _parse_hgca_votable_row("<TABLEDATA></TABLEDATA>", hip=1)


def test_parse_hgca_votable_row_raises_on_shape_mismatch():
    """A TR row with a different cell count than the FIELD list is a real
    schema-mismatch signal and should raise, not silently misassign
    values to the wrong column names."""
    malformed = """<?xml version="1.0"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
<RESOURCE><TABLE>
<FIELD name="HIP" datatype="int"/>
<FIELD name="Gaia" datatype="long"/>
<DATA><TABLEDATA><TR><TD>41926</TD></TR></TABLEDATA></DATA>
</TABLE></RESOURCE></VOTABLE>"""
    with pytest.raises(ValueError, match="TD cells"):
        _parse_hgca_votable_row(malformed, hip=41926)


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
