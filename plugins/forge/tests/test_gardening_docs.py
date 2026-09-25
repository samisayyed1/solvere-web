"""gardening-docs verify.py: the link checker catches a broken link (CONTRACTS.md §9)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def verify_mod():
    path = PLUGIN_ROOT / "skills" / "gardening-docs" / "scripts" / "verify.py"
    spec = importlib.util.spec_from_file_location("forge_skill_gardening_docs", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_broken_relative_link_is_caught(verify_mod, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("See [the other doc](./b.md) and [nowhere](./missing.md).\n")
    (tmp_path / "docs" / "b.md").write_text("# B\ncontent\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    broken = next(m for m in result["measurements"] if m["name"] == "broken_links")
    assert broken["value"] == 1
    assert broken["pass"] is False
    assert "missing.md" in broken["remediation"]


def test_valid_relative_links_pass(verify_mod, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("See [the other doc](./b.md#section-two).\n")
    (tmp_path / "docs" / "b.md").write_text("# B\n\n## Section Two\ncontent\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    broken = next(m for m in result["measurements"] if m["name"] == "broken_links")
    assert broken["value"] == 0


def test_broken_anchor_on_an_existing_file_is_caught(verify_mod, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("See [the other doc](./b.md#does-not-exist).\n")
    (tmp_path / "docs" / "b.md").write_text("# B\n\n## Real Section\ncontent\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    broken = next(m for m in result["measurements"] if m["name"] == "broken_links")
    assert broken["value"] == 1


def test_same_document_anchor_checked(verify_mod, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nSee [below](#missing-section).\n\n## Real Section\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    broken = next(m for m in result["measurements"] if m["name"] == "broken_links")
    assert broken["value"] == 1
    assert rc == 1


def test_external_links_are_never_checked(verify_mod, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "See [an external site](https://example.com/nope) and [mail](mailto:a@b.com).\n"
    )
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0


def test_stale_tool_version_marker_flagged(verify_mod, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "KiCad 9.9.9 is pinned. <!-- forge-tool-version: kicad-cli 9.9.9 -->\n"
    )
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    stale = next(m for m in result["measurements"] if m["name"] == "stale_tool_versions")
    assert stale["value"] == 1
    assert "kicad-cli" in stale["remediation"]


def test_matching_tool_version_marker_passes(verify_mod, tmp_path):
    manifest = json.loads((PLUGIN_ROOT / "toolchain" / "manifest.json").read_text())
    kicad = next(t for t in manifest["tools"] if t["id"] == "kicad-cli")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        f"KiCad {kicad['version']} is pinned. <!-- forge-tool-version: kicad-cli {kicad['version']} -->\n"
    )
    rc = verify_mod.main(["--project", str(tmp_path)])
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    stale = next(m for m in result["measurements"] if m["name"] == "stale_tool_versions")
    assert stale["value"] == 0


def test_rule_bullet_without_mechanism_flagged(verify_mod, tmp_path):
    (tmp_path / ".claude" / "rules").mkdir(parents=True)
    (tmp_path / ".claude" / "rules" / "mechanical.md").write_text(
        "# Mechanical rules\n\n"
        "- Only mechanical-engineer writes cad/, enforced by a PreToolUse hook.\n"
        "- Always use nice fillets.\n"
    )
    (tmp_path / "docs.md").write_text("nothing to link here\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    unenforced = next(m for m in result["measurements"] if m["name"] == "unenforced_rule_bullets")
    assert unenforced["value"] == 1
    assert "nice fillets" in unenforced["remediation"]


def test_rule_bullet_marked_advisory_passes(verify_mod, tmp_path):
    """A bullet with no hook/lint/check/gate can still pass if it says so honestly
    (M7: templates/project's own rules use this for genuinely unchecked guidance)."""
    (tmp_path / ".claude" / "rules").mkdir(parents=True)
    (tmp_path / ".claude" / "rules" / "mechanical.md").write_text(
        "# Mechanical rules\n\n"
        "- Only mechanical-engineer writes cad/, enforced by a PreToolUse hook.\n"
        "- Always use nice fillets (advisory -- no automated check for aesthetics).\n"
    )
    (tmp_path / "docs.md").write_text("nothing to link here\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    result = json.loads((tmp_path / "out/verify/gardening.docs.json").read_text())
    unenforced = next(m for m in result["measurements"] if m["name"] == "unenforced_rule_bullets")
    assert unenforced["value"] == 0
    assert rc == 0


def test_no_markdown_files_is_a_clean_skip(verify_mod, tmp_path):
    assert verify_mod.main(["--project", str(tmp_path)]) == 0
