"""drafting-drawings, general multi-view drawings (schema forge.drawing/2).

End-to-end on three example parts shipped with the skill (L bracket with
holes; flanged bushing with a boss and a counterbore, section A-A; enclosure
shell over two sheets with a section and a 4:1 detail), then one seeded-wrong
case per failure the check promises to catch (CONTRACTS.md §3, §9). Seeded
cases mostly corrupt the *output* DXF and re-run ``verify.py --recheck``, so
they prove the check reads the drawing back rather than trusting the generator.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("numpy")  # CAD-env only; canonical runner is ~/.forge/bin/forge-python
pytest.importorskip("build123d")

TESTS = Path(__file__).resolve().parent
SKILL = TESTS.parents[1] / "skills" / "drafting-drawings"
SCRIPTS = SKILL / "scripts"
EXAMPLE = SKILL / "examples" / "project"
VERIFY = SCRIPTS / "verify.py"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable
FREECADCMD = Path.home() / ".forge" / "bin" / "freecadcmd"
NAMES = ("l_bracket", "flanged_bushing", "enclosure")

for p in (str(SCRIPTS), str(TESTS.parents[1] / "lib")):
    if p not in sys.path:
        sys.path.insert(0, p)

needs_freecad = pytest.mark.skipif(not FREECADCMD.exists(), reason="freecadcmd not installed")


def _verify(project: Path, name: str | None = None, *extra: str) -> subprocess.CompletedProcess:
    args = [PY, str(VERIFY), "--project", str(project)]
    if name:
        args += ["--changed", f"cad/drawings/{name}.toml"]
    return subprocess.run(args + list(extra), capture_output=True, text=True, timeout=600)


def _result(project: Path, name: str) -> dict:
    return json.loads((project / "out" / "verify" / f"mech.drawing_{name}.json").read_text())


def _m(res: dict) -> dict:
    return {m["name"]: m for m in res["measurements"]}


@pytest.fixture(scope="session")
def generated(tmp_path_factory) -> Path:
    if not FREECADCMD.exists():
        pytest.skip("freecadcmd not installed")
    proj = tmp_path_factory.mktemp("drawings") / "project"
    shutil.copytree(EXAMPLE, proj)
    r = _verify(proj)
    assert r.returncode == 0, r.stdout + r.stderr
    return proj


@pytest.fixture
def project(generated, tmp_path) -> Path:
    """A private copy of the generated project (spec, params, model, out/)."""
    dst = tmp_path / "project"
    shutil.copytree(generated, dst)
    return dst


def _sheet(project: Path, name: str, i: int = 1) -> Path:
    return project / "out" / "drawings" / name / f"sheet{i}.dxf"


def _edit_dxf(path: Path, fn) -> None:
    import ezdxf
    doc = ezdxf.readfile(str(path))
    fn(doc)
    doc.saveas(str(path))


def _dim_text(doc, layer: str):
    for e in doc.modelspace().query("DIMENSION"):
        if e.dxf.layer == layer:
            return next(iter(doc.blocks.get(e.dxf.geometry).query("TEXT")))
    raise AssertionError(f"no DIMENSION on {layer}")


def _delete_layer(doc, layer: str, types: tuple[str, ...] | None = None) -> int:
    msp = doc.modelspace()
    victims = [e for e in msp if e.dxf.layer == layer and (types is None or e.dxftype() in types)]
    for e in victims:
        msp.delete_entity(e)
    return len(victims)


def _assert_fails(r, project: Path, name: str, measurement: str) -> dict:
    assert r.returncode == 1, r.stdout + r.stderr
    res = _result(project, name)
    assert res["status"] == "fail"
    m = _m(res)[measurement]
    assert m["pass"] is False, m
    assert len(m["remediation"]) >= 10
    return res


# --------------------------------------------------------------- happy path
@needs_freecad
@pytest.mark.slow
def test_all_three_example_parts_pass_with_every_view_and_dimension(generated):
    expected = {"l_bracket": (9, 1), "flanged_bushing": (9, 1), "enclosure": (9, 2)}
    for name, (n_dims, n_sheets) in expected.items():
        res = _result(generated, name)
        assert res["status"] == "pass", [m for m in res["measurements"] if not m["pass"]]
        m = _m(res)
        assert sum(1 for k in m if k.endswith("_drawing_vs_model")) == n_dims
        for i in range(1, n_sheets + 1):
            assert m[f"sheet{i}_reproducible"]["value"] == 0
            assert m[f"sheet{i}_projection_symbol"]["value"] == 1
            pdf = generated / "out" / "drawings" / name / f"sheet{i}.pdf"
            assert pdf.stat().st_size > 1000
            # printed to scale: the PDF page is the declared A3 sheet (420 x 297 mm)
            box = re.search(rb"MediaBox \[ ?0 0 ([\d.]+) ([\d.]+) ?\]", pdf.read_bytes())
            assert box and abs(float(box.group(1)) - 420 / 25.4 * 72) < 0.1 and abs(float(box.group(2)) - 297 / 25.4 * 72) < 0.1
        assert not (generated / "out" / "drawings" / name / f"sheet{n_sheets + 1}.dxf").exists()
    # section and detail views exist, with their markers, on the enclosure
    m = _m(_result(generated, "enclosure"))
    assert m["view_a_markers"]["pass"] and m["view_b_markers"]["pass"]
    assert m["view_a_extent_error"]["value"] <= 0.05


@needs_freecad
@pytest.mark.slow
def test_every_dimension_is_a_techdraw_dimension_within_0_01_mm_of_build123d(generated):
    for name in NAMES:
        rep = json.loads((generated / "out" / "drawings" / name / "report.json").read_text())
        for did, d in rep["dimensions"].items():
            td = d["techdraw"]
            assert td["method"] == "techdraw", (name, did, td)
            assert abs(td["raw_value"] - d["model_mm"]) <= 0.01, (name, did)
            assert abs(d["param_value_mm"] - d["model_mm"]) <= 0.01, (name, did)


@needs_freecad
@pytest.mark.slow
def test_dxf_independently_carries_values_tolerances_title_block_and_symbol(generated):
    import ezdxf
    from dxf_checks import dimension_texts, parse_dim_text, projection_method_drawn, texts_on
    doc = ezdxf.readfile(str(_sheet(generated, "l_bracket")))
    assert parse_dim_text(dimension_texts(doc, "Dim_base_length")[0]) == {
        "count": 1, "symbol": "linear", "nominal": 60.0, "style": "plusminus", "plus": 0.2, "minus": 0.2}
    hole = parse_dim_text(dimension_texts(doc, "Dim_base_hole_dia")[0])
    assert hole["count"] == 2 and hole["symbol"] == "diameter" and hole["plus"] == 0.1 and hole["minus"] == 0.0
    lim = parse_dim_text(dimension_texts(doc, "Dim_upright_hole_dia")[0])
    assert lim["style"] == "limits" and (lim["upper"], lim["lower"]) == (8.05, 7.95)
    tb = texts_on(doc, "TITLE_BLOCK")
    for field in ("L MOUNTING BRACKET", "FX-1001", "A", "EN AW-6061-T6 (example)", "mm", "ISO 2768-m", "forge",
                  "2026-09-25", "1:1", "SHEET 1 OF 1", "NOT FOR MANUFACTURE UNTIL SIGNED", "THIRD ANGLE PROJECTION"):
        assert field in tb, field
    assert projection_method_drawn(doc)[0] == "third"
    doc2 = ezdxf.readfile(str(_sheet(generated, "flanged_bushing")))
    assert projection_method_drawn(doc2)[0] == "first"
    layers = {e.dxf.layer for e in doc2.modelspace()}
    assert {"View_front", "View_top", "View_a", "View_iso", "HATCH_a", "SECTION_LINE_a", "FCF_bore_perpendicular"} <= layers


# ------------------------------------------------------ seeded-wrong: DXF
@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_critical_dimension_is_missing(project):
    _edit_dxf(_sheet(project, "l_bracket"), lambda d: _delete_layer(d, "Dim_height"))
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "dim_height_present")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_drawn_value_differs_from_the_model_by_more_than_0_01_mm(project):
    def bump(doc):
        t = _dim_text(doc, "Dim_base_length")
        assert t.dxf.text.startswith("60.00")
        t.dxf.text = t.dxf.text.replace("60.00", "60.02")
    _edit_dxf(_sheet(project, "l_bracket"), bump)
    r = _verify(project, "l_bracket", "--recheck")
    res = _assert_fails(r, project, "l_bracket", "dim_base_length_drawing_vs_model")
    assert abs(_m(res)["dim_base_length_drawing_vs_model"]["value"] - 0.02) < 1e-6


@needs_freecad
@pytest.mark.slow
def test_PASSES_value_check_at_display_rounding_below_0_01_mm(project):
    """0.005 mm of display error is inside the 0.01 mm limit -- the check is a tolerance, not string equality."""
    def nudge(doc):
        t = _dim_text(doc, "Dim_upright_hole_z")
        t.dxf.text = t.dxf.text.replace("35.00", "35.005")
    _edit_dxf(_sheet(project, "l_bracket"), nudge)
    _verify(project, "l_bracket", "--recheck")
    m = _m(_result(project, "l_bracket"))["dim_upright_hole_z_drawing_vs_model"]
    assert m["pass"] is True and abs(m["value"] - 0.005) < 1e-6


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_tolerance_is_missing(project):
    def strip(doc):
        t = _dim_text(doc, "Dim_width")
        t.dxf.text = t.dxf.text.split(" ")[0]
    _edit_dxf(_sheet(project, "l_bracket"), strip)
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "dim_width_tolerance")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_declared_view_is_missing(project):
    _edit_dxf(_sheet(project, "l_bracket"), lambda d: _delete_layer(d, "View_right"))
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "view_right_present")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_the_projection_symbol_is_missing(project):
    _edit_dxf(_sheet(project, "l_bracket"), lambda d: _delete_layer(d, "PROJECTION_SYMBOL"))
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "sheet1_projection_symbol")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_declared_projection_contradicts_the_symbol_and_view_arrangement(project):
    spec = project / "cad" / "drawings" / "l_bracket.toml"
    spec.write_text(spec.read_text().replace('projection = "third"', 'projection = "first"'))
    r = _verify(project, "l_bracket", "--recheck")
    res = _assert_fails(r, project, "l_bracket", "sheet1_projection_symbol")
    assert _m(res)["sheet1_view_arrangement"]["pass"] is False


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_title_block_field_is_missing(project):
    def drop(doc):
        msp = doc.modelspace()
        for e in [e for e in msp.query("TEXT") if e.dxf.layer == "TITLE_BLOCK" and e.dxf.text == "EN AW-6061-T6 (example)"]:
            msp.delete_entity(e)
    _edit_dxf(_sheet(project, "l_bracket"), drop)
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "sheet1_title_block_fields")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_the_drawing_is_not_reproducible(project):
    """Add one stray line on a layer no other check reads: every value, view and field still
    checks out, only the regenerate-and-compare step catches it. (A moved view edge is also
    caught by view_<id>_orientation.)"""
    def shift(doc):
        doc.modelspace().add_line((30, 30), (60, 45), dxfattribs={"layer": "0"})
    _edit_dxf(_sheet(project, "l_bracket"), shift)
    r = _verify(project, "l_bracket", "--recheck")
    res = _assert_fails(r, project, "l_bracket", "sheet1_reproducible")
    failing = [m["name"] for m in res["measurements"] if not m["pass"]]
    assert failing == ["sheet1_reproducible"], failing


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_section_marker_is_missing(project):
    _edit_dxf(_sheet(project, "flanged_bushing"), lambda d: _delete_layer(d, "SECTION_LINE_a"))
    r = _verify(project, "flanged_bushing", "--recheck")
    _assert_fails(r, project, "flanged_bushing", "view_a_markers")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_feature_control_frame_or_datum_symbol_is_missing(project):
    def drop(doc):
        assert _delete_layer(doc, "FCF_bore_perpendicular") > 0
        assert _delete_layer(doc, "DATUM_B") > 0
    _edit_dxf(_sheet(project, "flanged_bushing"), drop)
    r = _verify(project, "flanged_bushing", "--recheck")
    res = _assert_fails(r, project, "flanged_bushing", "gdt_bore_perpendicular_frame")
    assert _m(res)["datum_B_symbol"]["pass"] is False


@needs_freecad
@pytest.mark.slow
def test_FAILS_a_mirrored_view_even_though_its_size_is_right(project):
    """Front vs rear (or a mirrored export) has the same outline; the edge-position check catches it."""
    def mirror(doc):
        lines = [e for e in doc.modelspace().query("LINE") if e.dxf.layer == "View_front"]
        xs = [x for e in lines for x in (e.dxf.start[0], e.dxf.end[0])]
        c = (min(xs) + max(xs)) / 2
        for e in lines:
            e.dxf.start = (2 * c - e.dxf.start[0], e.dxf.start[1], 0)
            e.dxf.end = (2 * c - e.dxf.end[0], e.dxf.end[1], 0)
    _edit_dxf(_sheet(project, "l_bracket"), mirror)
    r = _verify(project, "l_bracket", "--recheck")
    res = _assert_fails(r, project, "l_bracket", "view_front_orientation")
    assert _m(res)["view_front_extent_error"]["pass"] is True


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_view_layer_is_frozen(project):
    _edit_dxf(_sheet(project, "l_bracket"), lambda d: d.layers.get("View_top").freeze())
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "sheet1_reproducible")


@needs_freecad
@pytest.mark.slow
def test_FAILS_on_a_second_conflicting_callout(project):
    def dup(doc):
        doc.layers.add("DIMTXT_width")
        doc.modelspace().add_text("40.50 %%p0.20", dxfattribs={"layer": "DIMTXT_width", "insert": (20, 20)})
    _edit_dxf(_sheet(project, "l_bracket"), dup)
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "dim_width_present")


@needs_freecad
@pytest.mark.slow
def test_FAILS_a_shifted_limit_even_inside_display_rounding(project):
    def shift(doc):
        t = _dim_text(doc, "Dim_upright_hole_dia")
        assert t.dxf.text == "%%c8.05/7.95"
        t.dxf.text = "%%c8.06/7.95"
    _edit_dxf(_sheet(project, "l_bracket"), shift)
    r = _verify(project, "l_bracket", "--recheck")
    res = _assert_fails(r, project, "l_bracket", "dim_upright_hole_dia_tolerance")
    assert _m(res)["dim_upright_hole_dia_drawing_vs_model"]["pass"] is True  # 0.01 off: at the limit, tolerance catches it


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_dimension_geometry_in_the_dxf_is_moved(project):
    """The TechDraw length is re-read from the DXF extension-line origins, not only from layout.json."""
    def move(doc):
        e = next(e for e in doc.modelspace().query("DIMENSION") if e.dxf.layer == "Dim_base_length")
        p = e.dxf.defpoint3
        e.dxf.defpoint3 = (p[0] + 0.5, p[1], 0)
    _edit_dxf(_sheet(project, "l_bracket"), move)
    r = _verify(project, "l_bracket", "--recheck")
    _assert_fails(r, project, "l_bracket", "dim_base_length_dxf_geometry_vs_model")


@needs_freecad
@pytest.mark.slow
def test_changed_params_file_rechecks_the_drawings_that_depend_on_it(project):
    params = project / "params" / "params.toml"
    params.write_text(params.read_text().replace("[bracket.base_length]\nvalue = 60.0", "[bracket.base_length]\nvalue = 62.0"))
    r = subprocess.run([PY, str(VERIFY), "--project", str(project), "--changed", "params/params.toml", "--recheck"],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[FAIL] mech.drawing_l_bracket" in r.stdout
    assert "[SKIP]" not in r.stdout


# ------------------------------------------------- seeded-wrong: model/spec
@needs_freecad
@pytest.mark.slow
def test_FAILS_a_stale_drawing_after_params_change(project):
    """params change, drawing not regenerated: the model now measures 62 mm, the sheet still says 60."""
    params = project / "params" / "params.toml"
    params.write_text(params.read_text().replace("[bracket.base_length]\nvalue = 60.0", "[bracket.base_length]\nvalue = 62.0"))
    r = _verify(project, "l_bracket", "--recheck")
    res = _assert_fails(r, project, "l_bracket", "dim_base_length_drawing_vs_model")
    assert _m(res)["sheet1_reproducible"]["pass"] is False


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_the_model_is_not_built_from_params(project):
    """A part that ignores its params value: TechDraw and build123d agree with each other, not with params."""
    part = project / "cad" / "l_bracket.py"
    part.write_text(part.read_text().replace('L = p(params, "bracket.base_length")', 'L = p(params, "bracket.base_length") + 0.3'))
    r = _verify(project, "l_bracket")
    res = _assert_fails(r, project, "l_bracket", "dim_base_length_params_vs_model")
    m = _m(res)
    assert m["dim_base_length_drawing_vs_model"]["pass"] is True  # the drawing faithfully shows the (wrong) model
    assert m["dim_base_length_techdraw_vs_model"]["pass"] is True


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_a_selector_matches_no_feature(project):
    spec = project / "cad" / "drawings" / "l_bracket.toml"
    txt = spec.read_text().replace('of = { cylinder = "X", near = ["bracket.thickness/2", "bracket.width/2 + bracket.upright_hole_dia/2", "bracket.upright_hole_z"] }',
                                   'of = { cylinder = "X", near = [30, 0, 3] }', 1)
    spec.write_text(txt)
    r = _verify(project, "l_bracket")
    _assert_fails(r, project, "l_bracket", "dim_upright_hole_dia_resolved")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_callout_count_disagrees_with_the_model(project):
    spec = project / "cad" / "drawings" / "l_bracket.toml"
    spec.write_text(spec.read_text().replace('type = "diameter"\ncount = 2', 'type = "diameter"\ncount = 3', 1))
    r = _verify(project, "l_bracket")
    _assert_fails(r, project, "l_bracket", "dim_base_hole_dia_feature_count")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_drawing_tolerance_disagrees_with_params(project):
    spec = project / "cad" / "drawings" / "l_bracket.toml"
    spec.write_text(spec.read_text().replace('to = { plane = "Y", at = "max" }\ntol = 0.2', 'to = { plane = "Y", at = "max" }\ntol = 0.3', 1))
    r = _verify(project, "l_bracket")
    _assert_fails(r, project, "l_bracket", "dim_width_tolerance_vs_params")


@needs_freecad
@pytest.mark.slow
def test_FAILS_withdrawn_iso_2768_geometric_class(project):
    spec = project / "cad" / "drawings" / "enclosure.toml"
    spec.write_text(spec.read_text().replace('general_tolerance = "ISO 2768-m"', 'general_tolerance = "ISO 2768-mK"'))
    r = _verify(project, "enclosure", "--recheck")
    _assert_fails(r, project, "enclosure", "general_tolerance_class_current")


@needs_freecad
@pytest.mark.slow
def test_annotation_fallback_for_a_hidden_feature_is_still_verified(project):
    """Pilot holes are blind from above: seen from below there is no circle to attach a TechDraw
    dimension to, so the callout falls back to annotation text -- and is still checked."""
    spec = project / "cad" / "drawings" / "enclosure.toml"
    s = spec.read_text()
    s = s.replace('sheet_size = "A3"', 'sheet_size = "A2"')
    s = s.replace('views = ["front", "top", "right", "iso"]', 'views = ["front", "top", "right", "iso", "bottom"]')
    s = s.replace('[[view]]\nid = "iso"', '[[view]]\nid = "bottom"\nkind = "bottom"\n\n[[view]]\nid = "iso"')
    s = s.replace('requirement = "REQ-MECH-023"\nview = "a"\ntype = "diameter"\ncount = 2\nside = "above"',
                  'requirement = "REQ-MECH-023"\nview = "bottom"\ntype = "diameter"\ncount = 2')
    spec.write_text(s)
    # without an explicit opt-in the fallback itself fails: no independent TechDraw value
    r = _verify(project, "enclosure")
    _assert_fails(r, project, "enclosure", "dim_pilot_dia_annotation_fallback")
    spec.write_text(s.replace('view = "bottom"\ntype = "diameter"\ncount = 2', 'view = "bottom"\ntype = "diameter"\ncount = 2\nallow_annotation = true'))
    r = _verify(project, "enclosure")
    assert r.returncode == 0, r.stdout + r.stderr
    layout = json.loads((project / "out" / "drawings" / "enclosure" / "layout.json").read_text())
    assert layout["dims"]["pilot_dia"]["method"] == "annotation"
    m = _m(_result(project, "enclosure"))
    assert m["dim_pilot_dia_present"]["pass"] and m["dim_pilot_dia_drawing_vs_model"]["pass"]
    assert "dim_pilot_dia_techdraw_vs_model" not in m

    def bump(doc):
        t = next(e for e in doc.modelspace().query("TEXT") if e.dxf.layer == "DIMTXT_pilot_dia")
        t.dxf.text = t.dxf.text.replace("3.20", "3.25")
    _edit_dxf(_sheet(project, "enclosure"), bump)
    r = _verify(project, "enclosure", "--recheck")
    _assert_fails(r, project, "enclosure", "dim_pilot_dia_drawing_vs_model")


@needs_freecad
@pytest.mark.slow
def test_FAILS_when_views_do_not_fit_the_sheet(project):
    spec = project / "cad" / "drawings" / "l_bracket.toml"
    spec.write_text(spec.read_text().replace('sheet_size = "A3"', 'sheet_size = "A4"').replace('scale = "1:1"', 'scale = "2:1"'))
    r = _verify(project, "l_bracket")
    _assert_fails(r, project, "l_bracket", "sheet1_layout_overflow")


# --------------------------------------------------------- spec errors (2)
@pytest.mark.parametrize("old,new,why", [
    ('datums = ["A", "B"]', 'datums = ["A", "C"]', "undeclared datum"),
    ('tol = 0.2\n\n[[dimension]]\nid = "height"', '\n[[dimension]]\nid = "height"', "missing tolerance"),
    ('projection = "third"', 'projection = "second"', "bad projection"),
    ('units = "mm"', 'units = "in"', "non-mm units"),
    ('id = "width"\nparam = "bracket.width"\nrequirement = "REQ-MECH-004"\nview = "top"',
     'id = "width"\nparam = "bracket.width"\nrequirement = "REQ-MECH-004"\nview = "iso"', "dimension on pictorial view"),
    ('id = "width"\nparam = "bracket.width"\nrequirement = "REQ-MECH-004"\nview = "top"',
     'id = "width"\nparam = "bracket.width"\nrequirement = "REQ-MECH-004"\nview = "front"', "axis not in view plane"),
    ('tol = { plus = 0.1, minus = 0.1 }', 'tol = { plus = 0.1, minus = 0.1 }\ndecimals = 1', "too few decimals for 0.01 mm"),
    # S14: a negative tol.minus (or .plus) must FAIL even when plus+minus still nets
    # positive -- 0.3 + (-0.1) = 0.2 > 0 used to slip past the old plus+minus <= 0 check.
    ('tol = { plus = 0.1, minus = 0.1 }', 'tol = { plus = 0.3, minus = -0.1 }', "negative tolerance magnitude"),
    ('scale = "1:1"', 'scale = "1:0"', "zero in scale"),
    ('param = "bracket.height"', 'param = "bracket.no_such_key"', "unknown params key"),
    ('views = ["front", "top", "right", "iso"]', 'views = ["front", "top", "iso"]', "view not placed on a sheet"),
    ('tol = { plus = 0.1, minus = 0.1 }', 'tol = { plus = 0.1, minus = 0.1 }\ndecimals = "x"', "non-numeric decimals"),
])
def test_ERRORS_exit_2_on_malformed_spec(tmp_path, old, new, why):
    proj = tmp_path / "project"
    shutil.copytree(EXAMPLE, proj)
    spec = proj / "cad" / "drawings" / "l_bracket.toml"
    s = spec.read_text()
    assert old in s, why
    spec.write_text(s.replace(old, new, 1))
    r = _verify(proj, "l_bracket")
    assert r.returncode == 2, (why, r.stdout + r.stderr)
    assert _result(proj, "l_bracket")["status"] == "error"


# ------------------------------------------------------------ unit level
def test_dimension_text_grammar_round_trips():
    from drawspec import format_dim_text, parse_tol
    from dxf_checks import parse_dim_text
    base = {"type": "linear", "decimals": 2, "count": 1}
    cases = [
        ({**base, "tol": parse_tol(0.1, "t")}, "25.40 %%p0.10", {"plus": 0.1, "minus": 0.1}),
        ({**base, "type": "diameter", "count": 4, "tol": parse_tol({"plus": 0.1, "minus": 0}, "t")}, "4X %%c5.50 +0.10/0",
         {"plus": 0.1, "minus": 0.0}),
        ({**base, "type": "radius", "tol": parse_tol({"plus": 0.05, "minus": 0.02}, "t")}, "R3.00 +0.05/-0.02",
         {"plus": 0.05, "minus": 0.02}),
    ]
    values = [25.4, 5.5, 3.0]
    for (dim, want_text, tol), v in zip(cases, values):
        fmt, arbitrary = format_dim_text(dim, v)
        assert not arbitrary
        text = fmt.replace("%.2f", f"{v:.2f}")
        assert text == want_text
        p = parse_dim_text(text)
        assert p["nominal"] == v and p["plus"] == tol["plus"] and p["minus"] == tol["minus"]
    lim, arbitrary = format_dim_text({**base, "type": "diameter", "decimals": 3,
                                      "tol": parse_tol({"plus": 0.018, "minus": 0.0, "style": "limits"}, "t")}, 12.0)
    assert arbitrary and lim == "%%c12.018/12.000"
    p = parse_dim_text(lim)
    assert p["style"] == "limits" and p["upper"] == 12.018 and p["lower"] == 12.0
    assert parse_dim_text("60.00") == {"count": 1, "symbol": "linear", "nominal": 60.0, "style": None}
    assert parse_dim_text("about sixty") is None


def test_projection_symbol_geometry_is_read_not_its_label(tmp_path):
    import ezdxf
    from compose_sheet import projection_symbol
    from dxf_checks import projection_method_drawn
    for method in ("first", "third"):
        doc = ezdxf.new()
        doc.linetypes.add("FORGE_CENTER", pattern=[20.0, 12.0, -3.0, 2.0, -3.0])
        projection_symbol(doc.modelspace(), 100, 100, method)
        assert projection_method_drawn(doc)[0] == method
    doc = ezdxf.new()
    doc.linetypes.add("FORGE_CENTER", pattern=[20.0, 12.0, -3.0, 2.0, -3.0])
    projection_symbol(doc.modelspace(), 100, 100, "third")
    for c in doc.modelspace().query("CIRCLE"):
        c.dxf.center = (c.dxf.center[0] - 40, c.dxf.center[1])  # move the end view to the other side
    assert projection_method_drawn(doc)[0] == "first"


def test_params_expressions_are_arithmetic_only():
    from drawspec import SpecError, eval_expr
    params = {"a": {"b": {"value": 4.0, "unit": "mm"}}}
    assert eval_expr("a.b/2 + 1", params, "t") == 3.0
    assert eval_expr(-2.5, params, "t") == -2.5
    for bad in ("__import__('os')", "a.b ** 2", "open", "a.c"):
        with pytest.raises(SpecError):
            eval_expr(bad, params, "t")
