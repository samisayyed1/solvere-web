"""``forge sync-template`` (D4, review #2 addendum): a scaffolded project
never silently drifts from -- or gets silently overwritten by -- the
template it came from.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge import gitbaseline
from forge.commands import sync_template


def _mini_template(tpl: Path) -> None:
    tpl.mkdir(parents=True)
    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\nRoot: ${FORGE_ROOT}\n")
    (tpl / "RISKS.md").write_text("# Risks\n\n(none yet)\n")


def _scaffold(tpl: Path, target: Path, *, name: str = "Widget", forge_root: Path | None = None) -> None:
    target.mkdir(parents=True)
    written = []
    for rel in ("CLAUDE.md", "RISKS.md"):
        text = (tpl / rel).read_text().replace("{{PROJECT_NAME}}", name).replace(
            "${FORGE_ROOT}", str(forge_root or tpl))
        (target / rel).write_text(text)
        written.append(target / rel)
    gitbaseline.write_scaffold_manifest(target, templates_dir=tpl, written=written,
                                        project_name=name, forge_root=forge_root or tpl)


@pytest.fixture()
def tpl_and_project(tmp_path):
    tpl = tmp_path / "templates" / "project"
    project = tmp_path / "product"
    _mini_template(tpl)
    _scaffold(tpl, project)
    return tpl, project


def test_freshly_scaffolded_project_has_no_drift(tpl_and_project):
    tpl, project = tpl_and_project
    report = sync_template.diff(project, templates_dir=tpl, forge_root=tpl)
    assert report["new"] == [] and report["drifted"] == [] and report["conflicts"] == []
    assert sorted(report["up_to_date"]) == ["CLAUDE.md", "RISKS.md"]


def test_seeded_wrong_a_user_edit_is_reported_as_a_conflict_never_overwritten(tpl_and_project):
    """Seeded wrong: RISKS.md is edited by the user AND the template also
    changes. `--write` must leave the user's edit alone."""
    tpl, project = tpl_and_project
    (project / "RISKS.md").write_text("# Risks\n\n- R1: seals may leak (user-added)\n")
    (tpl / "RISKS.md").write_text("# Risks\n\n(template default, now with a legend)\n")

    report = sync_template.diff(project, templates_dir=tpl, forge_root=tpl)
    assert report["conflicts"] == ["RISKS.md"]
    assert report["drifted"] == [] and report["new"] == []

    written = sync_template.apply_write(project, report)
    assert written == []  # a conflict is never auto-written
    assert "user-added" in (project / "RISKS.md").read_text()


def test_an_unmodified_file_drifts_and_write_refreshes_it(tpl_and_project):
    """The project never touched CLAUDE.md; the template's CLAUDE.md changes.
    That IS safe to refresh."""
    tpl, project = tpl_and_project
    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\nRoot: ${FORGE_ROOT}\nNew guidance line.\n")

    report = sync_template.diff(project, templates_dir=tpl, forge_root=tpl)
    assert report["drifted"] == ["CLAUDE.md"]
    assert report["conflicts"] == []

    written = sync_template.apply_write(project, report)
    assert written == ["CLAUDE.md"]
    assert "New guidance line." in (project / "CLAUDE.md").read_text()
    assert "Widget" in (project / "CLAUDE.md").read_text()  # substitution still applied

    # re-diffing now reports it as up to date, and the manifest was updated
    report2 = sync_template.diff(project, templates_dir=tpl, forge_root=tpl)
    assert "CLAUDE.md" not in report2["drifted"] and "CLAUDE.md" not in report2["conflicts"]
    manifest = gitbaseline.read_scaffold_manifest(project)
    assert manifest["files"]["CLAUDE.md"] == sync_template._sha256((project / "CLAUDE.md").read_bytes())


def test_a_new_template_file_is_reported_and_added_on_write(tpl_and_project):
    tpl, project = tpl_and_project
    (tpl / "SAFETY.md").write_text("# Safety notes\n")

    report = sync_template.diff(project, templates_dir=tpl, forge_root=tpl)
    assert report["new"] == ["SAFETY.md"]
    assert not (project / "SAFETY.md").exists()

    written = sync_template.apply_write(project, report)
    assert written == ["SAFETY.md"]
    assert (project / "SAFETY.md").read_text() == "# Safety notes\n"


def test_missing_scaffold_manifest_reports_every_differing_file_as_a_conflict(tmp_path):
    """No .forge/scaffold.json (an old project, or it was deleted): nothing
    can be proven unmodified, so a differing file is a conflict, never
    silently written."""
    tpl = tmp_path / "templates" / "project"
    project = tmp_path / "product"
    _mini_template(tpl)
    project.mkdir(parents=True)
    (project / "CLAUDE.md").write_text("# Widget\nRoot: x\n")  # written by hand, no manifest

    report = sync_template.diff(project, templates_dir=tpl, forge_root=tpl)
    assert report["has_manifest"] is False
    assert "CLAUDE.md" in report["conflicts"]
    assert "RISKS.md" in report["new"]  # never existed in the project: safe to add, not a conflict
    written = sync_template.apply_write(project, report)
    assert written == ["RISKS.md"]
    assert (project / "CLAUDE.md").read_text() == "# Widget\nRoot: x\n"  # the conflict was left alone


def test_cli_write_then_dry_run_is_clean(tpl_and_project, capsys):
    from forge.cli import main
    tpl, project = tpl_and_project
    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\nRoot: ${FORGE_ROOT}\nupdated\n")
    code = main(["sync-template", "--project", str(project), "--templates", str(tpl), "--write"],
               repo_root=tpl)
    assert code == 0
    capsys.readouterr()
    code = main(["sync-template", "--project", str(project), "--templates", str(tpl), "--json"], repo_root=tpl)
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data["drifted"] == [] and data["conflicts"] == []
