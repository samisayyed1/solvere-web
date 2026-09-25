"""Forge must stay product-agnostic: no product identifiers inside the plugin or template.

The denylist (security/product-denylist.txt) is maintained per product. This test is
the mechanism that enforces the separation; it fails on the first leak.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCOPES = ["plugins/forge", "templates", "docs/standards", ".claude-plugin"]
SKIP_PARTS = {".pytest_cache", "__pycache__", "node_modules", ".venv"}


def _patterns() -> list[re.Pattern[str]]:
    lines = (REPO / "security/product-denylist.txt").read_text().splitlines()
    return [re.compile(l.strip(), re.I) for l in lines if l.strip() and not l.lstrip().startswith("#")]


def _leaks(root: Path, patterns: list[re.Pattern[str]]) -> list[str]:
    hits = []
    for path in root.rglob("*"):
        if not path.is_file() or SKIP_PARTS & set(path.parts) or path.suffix in {".png", ".step", ".stl", ".pdf"}:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if any(p.search(line) for p in patterns):
                hits.append(f"{path.relative_to(REPO) if REPO in path.parents else path}:{n}: {line.strip()[:120]}")
    return hits


def test_forge_contains_no_product_identifiers():
    pats = _patterns()
    hits = [h for s in SCOPES for h in _leaks(REPO / s, pats)]
    assert not hits, "product identifiers leaked into Forge; move them to the product folder:\n" + "\n".join(hits)


def test_check_catches_a_seeded_leak(tmp_path):
    seeded = "Default radar: " + "MR60" + "FDA2 mounted on the ceiling " + "pod\n"  # split so this file stays clean
    (tmp_path / "skill.md").write_text(seeded)
    assert len(_leaks(tmp_path, _patterns())) == 1
