"""Smoke test for the CAD env: build, measure, export, mesh, render. Exit 0 = pass."""
import math
import pathlib
import sys
import tempfile

from build123d import Box, Cylinder, export_step, export_stl


def main() -> int:
    length, width, height, dia = 20.0, 10.0, 5.0, 3.0  # mm
    part = Box(length, width, height) - Cylinder(dia / 2, height)
    expected = length * width * height - math.pi * (dia / 2) ** 2 * height  # mm^3
    rel_err = abs(part.volume - expected) / expected
    out = pathlib.Path(tempfile.mkdtemp(prefix="forge-smoke-cad-"))
    export_step(part, str(out / "box.step"))
    export_stl(part, str(out / "box.stl"))

    import gmsh
    gmsh.initialize()
    gmsh.finalize()

    import pyvista as pv
    pv.OFF_SCREEN = True
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(pv.read(str(out / "box.stl")))
    plotter.screenshot(str(out / "box.png"))
    plotter.close()

    step_b = (out / "box.step").stat().st_size
    png_b = (out / "box.png").stat().st_size
    ok = rel_err < 1e-3 and step_b > 0 and png_b > 1000
    # Negative control: the same check against a 1 % wrong expectation must fail.
    wrong = expected * 1.01
    assert abs(part.volume - wrong) / wrong >= 1e-3, "negative control: check cannot fail"
    print(f"volume={part.volume:.4f} mm3 expected={expected:.4f} mm3 rel_err={rel_err:.2e} "
          f"step={step_b} B png={png_b} B out={out} -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
