"""DXF -> PDF, headless (ADR-001 §15.3: TechDraw's own PDF/SVG page export
needs a GUI -- issue #5710 -- but full-page DXF export works headlessly; this
converts that DXF to a PDF a human can open without FreeCAD). Runs under
``forge-python`` (ezdxf + matplotlib), not ``freecadcmd``.

With ``paper=(width_mm, height_mm)`` the PDF page is exactly the sheet size
and the drawing prints at its stated scale (1 DXF mm = 1 paper mm). With
``text_layer=True`` every TEXT/DIMENSION string is also written as an
invisible PDF text object (standard-14 Helvetica, like an OCR layer), so the
PDF is searchable and ``dxf_checks.pdf_strings`` can read the values back --
ezdxf draws the visible text as vector outlines, which carry no text. The
output is byte-reproducible (no creation date).
"""
from __future__ import annotations

import re
import zlib
from pathlib import Path

MM_PER_IN = 25.4
_CODES = {"%%c": "Ø", "%%p": "±", "%%d": "°", "%%C": "Ø", "%%P": "±", "%%D": "°"}


def decode_codes(text: str) -> str:
    for k, v in _CODES.items():
        text = text.replace(k, v)
    return text


def _all_strings(doc) -> list[tuple[str, float, float]]:
    out = []
    msp = doc.modelspace()
    for e in msp.query("TEXT"):
        out.append((e.dxf.text, float(e.dxf.insert[0]), float(e.dxf.insert[1])))
    for e in msp.query("MTEXT"):
        out.append((e.plain_text(), float(e.dxf.insert[0]), float(e.dxf.insert[1])))
    for e in msp.query("DIMENSION"):
        blk = doc.blocks.get(e.dxf.geometry) if e.dxf.hasattr("geometry") else None
        for t in (blk.query("TEXT") if blk is not None else []):
            out.append((t.dxf.text, float(t.dxf.insert[0]), float(t.dxf.insert[1])))
    return out


def dxf_to_pdf(dxf_path: Path, pdf_path: Path, paper: tuple[float, float] | None = None,
               text_layer: bool = False) -> Path:
    import logging

    import ezdxf
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.use14corefonts"] = True
    matplotlib.rcParams["svg.hashsalt"] = "forge"
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    if paper:
        fig = plt.figure(figsize=(paper[0] / MM_PER_IN, paper[1] / MM_PER_IN))
    else:
        fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax, adjust_figure=not paper)  # keep the sheet size when printing to scale
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK) if paper else Configuration()
    Frontend(ctx, backend, config=cfg).draw_layout(msp, finalize=True)
    if paper:
        fig.set_size_inches(paper[0] / MM_PER_IN, paper[1] / MM_PER_IN)
        ax.set_position([0, 0, 1, 1])
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(0, paper[0])
        ax.set_ylim(0, paper[1])
    if text_layer:
        for text, x, y in _all_strings(doc):
            ax.text(x, y, decode_codes(text), alpha=0.0, fontsize=4, family="Helvetica")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(pdf_path), metadata={"CreationDate": None, "Creator": "forge drafting-drawings", "Producer": "matplotlib"})
    plt.close(fig)
    return pdf_path


def pdf_strings(pdf_path: Path) -> list[str]:
    """Text-layer strings of a PDF written by this module (standard-14 fonts,
    literal strings in Flate/plain content streams). Not a general PDF parser."""
    data = Path(pdf_path).read_bytes()
    out: list[str] = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        s = m.group(1)
        try:
            s = zlib.decompress(s)
        except zlib.error:
            pass
        for lit in re.findall(rb"\(((?:\\.|[^\\)])*)\)\s*Tj", s):
            lit = re.sub(rb"\\([()\\])", rb"\1", lit)
            out.append(lit.decode("latin-1"))
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dxf", type=Path)
    ap.add_argument("pdf", type=Path)
    ns = ap.parse_args()
    dxf_to_pdf(ns.dxf, ns.pdf)
    print(f"OK {ns.pdf}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
