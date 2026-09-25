"""``forge lint manifest`` (ADR-001 SS3, CONTRACTS.md SS1): plugin packaging
hygiene.

- ``plugins/forge/.claude-plugin/plugin.json`` must not declare ``hooks``
  or ``agents`` keys -- declaring them double-loads hooks and hides agents
  from ``plugin details`` (ADR-001 SS3); the default component folders are
  auto-discovered instead.
- the repo-root marketplace's ``name`` must not collide with a reserved
  marketplace name.
- every marketplace plugin's ``source`` directory must actually exist.

Both manifest files are owned by other Forge builders in this parallel
build, so a missing file is a ``skip``, never a ``fail``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..checks import CheckResult

__all__ = ["lint_manifest", "RESERVED_MARKETPLACE_NAMES"]

FORBIDDEN_PLUGIN_JSON_KEYS = {"hooks", "agents"}
RESERVED_MARKETPLACE_NAMES = {"claude-plugins-official"}


def _is_reserved(name) -> bool:
    if not isinstance(name, str) or not name:
        return False
    return name in RESERVED_MARKETPLACE_NAMES or name.lower().startswith("anthropic")


def lint_manifest(plugin_root: Path, repo_root: Path) -> list[CheckResult]:
    plugin_root = Path(plugin_root)
    repo_root = Path(repo_root)
    results: list[CheckResult] = []

    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        results.append(
            CheckResult(
                id="manifest.plugin_json",
                status="skip",
                rule="plugin.json exists",
                measured=str(plugin_json),
                expected="present (owned by another Forge builder)",
            )
        )
    else:
        try:
            data = json.loads(plugin_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append(
                CheckResult(
                    id="manifest.plugin_json_parse",
                    status="fail",
                    rule="plugin.json is valid JSON",
                    measured=str(exc),
                    expected="valid JSON",
                    fix=f"Fix the JSON syntax in {plugin_json}.",
                )
            )
            data = None
        if isinstance(data, dict):
            bad_keys = sorted(set(data) & FORBIDDEN_PLUGIN_JSON_KEYS)
            if bad_keys:
                results.append(
                    CheckResult(
                        id="manifest.no_hooks_agents_keys",
                        status="fail",
                        rule=(
                            "plugin.json must not declare 'hooks' or 'agents' keys -- they double-load hooks.json "
                            "and hide agents from `plugin details` (ADR-001 SS3); use the default component folders"
                        ),
                        measured=bad_keys,
                        expected="neither key present",
                        fix=f"Remove {', '.join(bad_keys)} from {plugin_json}.",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        id="manifest.no_hooks_agents_keys",
                        status="pass",
                        rule="plugin.json has no hooks/agents keys",
                        measured=sorted(data),
                        expected="no hooks/agents keys",
                    )
                )

    marketplace_json = repo_root / ".claude-plugin" / "marketplace.json"
    if not marketplace_json.exists():
        results.append(
            CheckResult(
                id="manifest.marketplace_json",
                status="skip",
                rule="marketplace.json exists",
                measured=str(marketplace_json),
                expected="present (owned by another Forge builder)",
            )
        )
        return results

    try:
        mdata = json.loads(marketplace_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        results.append(
            CheckResult(
                id="manifest.marketplace_json_parse",
                status="fail",
                rule="marketplace.json is valid JSON",
                measured=str(exc),
                expected="valid JSON",
                fix=f"Fix the JSON syntax in {marketplace_json}.",
            )
        )
        return results

    if not isinstance(mdata, dict):
        results.append(
            CheckResult(
                id="manifest.marketplace_json_parse",
                status="fail",
                rule="marketplace.json's top level is a JSON object",
                measured=type(mdata).__name__,
                expected="object",
                fix=f"Fix {marketplace_json} to be a top-level JSON object.",
            )
        )
        return results

    name = mdata.get("name")
    if _is_reserved(name):
        results.append(
            CheckResult(
                id="manifest.marketplace_name",
                status="fail",
                rule="marketplace name must not collide with a reserved name (claude-plugins-official, anthropic*)",
                measured=name,
                expected="not reserved",
                fix=f"Rename the marketplace in {marketplace_json} away from {name!r}.",
            )
        )
    else:
        results.append(
            CheckResult(
                id="manifest.marketplace_name",
                status="pass",
                rule="marketplace name is not reserved",
                measured=name,
                expected="not reserved",
            )
        )

    plugins = mdata.get("plugins")
    if isinstance(plugins, list):
        missing = []
        checked = []
        for entry in plugins:
            src = entry.get("source") if isinstance(entry, dict) else None
            if not src or not isinstance(src, str):
                continue
            resolved = Path(src) if Path(src).is_absolute() else (repo_root / src)
            checked.append(src)
            if not resolved.resolve().exists():
                missing.append(src)
        if missing:
            results.append(
                CheckResult(
                    id="manifest.plugin_sources_exist",
                    status="fail",
                    rule="every marketplace plugin 'source' directory exists",
                    measured=missing,
                    expected="all sources resolve to a directory",
                    fix=f"Create or fix the referenced source dir(s): {', '.join(missing)}.",
                )
            )
        elif checked:
            results.append(
                CheckResult(
                    id="manifest.plugin_sources_exist",
                    status="pass",
                    rule="every marketplace plugin 'source' directory exists",
                    measured=checked,
                    expected="all resolve",
                )
            )

    return results
