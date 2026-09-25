"""Small, dependency-free validators used by the template tests.

These are test-support helpers, not part of the Forge CLI -- they exist so
that each protection asserted by the template tests can be proven to catch
a violation, not only shown to pass on the golden scaffolded output.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

# A hard-coded absolute home directory (macOS or Linux) baked into a portable
# template file -- m2 (review #1): templates/project/.mcp.json had
# /Users/samisayyed/.forge/... hard-coded, so it only worked on the machine
# that authored it. `${FORGE_ROOT}` (scaffold-time substituted) and
# `${HOME}`/`${CLAUDE_PROJECT_DIR}` (Claude Code's own .mcp.json env-var
# expansion, per code.claude.com/docs/en/mcp) are both fine; a literal
# /Users/<name> or /home/<name> path is not.
_HARDCODED_HOME_PATH = re.compile(r"/(?:Users|home)/[^/\"'\s]+/")


def hardcoded_home_paths(text: str) -> list[str]:
    """Every hard-coded /Users/<name>/... or /home/<name>/... path found."""
    return _HARDCODED_HOME_PATH.findall(text)

REQUIRED_VERIFY_ENTRYPOINTS = {
    "writing-requirements",
    "tracing-requirements",
    "modeling-systems",
    "verifying-geometry",
    "checking-dfm",
    "stacking-tolerances",
    "running-fea",
    "designing-circuits",
    "checking-ecad",
    "building-firmware",
    "gardening-docs",
}


def claude_md_line_count(path: Path) -> int:
    return len(Path(path).read_text(encoding="utf-8").splitlines())


def rules_missing_paths(rules_dir: Path) -> list[str]:
    """Return the filenames of any `.md` rule under ``rules_dir`` whose YAML
    frontmatter has no `paths:` key."""
    missing: list[str] = []
    for md in sorted(Path(rules_dir).glob("*.md")):
        text = md.read_text(encoding="utf-8")
        if not text.startswith("---"):
            missing.append(md.name)
            continue
        end = text.find("\n---", 3)
        frontmatter = text[3:end] if end != -1 else text[3:]
        if "paths:" not in frontmatter:
            missing.append(md.name)
    return missing


def settings_missing_required(settings: dict) -> list[str]:
    """Return a list of human-readable requirement names not met by a
    `.claude/settings.json` dict (ADR-001 §5, CONTRACTS.md)."""
    missing: list[str] = []
    perms = settings.get("permissions", {})
    deny = perms.get("deny", [])
    ask = perms.get("ask", [])
    sandbox = settings.get("sandbox", {})

    if not any("ssh" in rule for rule in deny):
        missing.append("permissions.deny: no credential-path rule (~/.ssh)")
    if "Agent(fork)" not in deny:
        missing.append("permissions.deny: missing Agent(fork)")
    if not any("git push" in rule for rule in ask):
        missing.append("permissions.ask: missing a git push rule")
    if not any("gh pr merge" in rule for rule in ask):
        missing.append("permissions.ask: missing a gh pr merge rule")
    if sandbox.get("enabled") is not True:
        missing.append("sandbox.enabled must be true")
    if sandbox.get("failIfUnavailable") is not True:
        missing.append("sandbox.failIfUnavailable must be true")
    if sandbox.get("allowUnsandboxedCommands") is not False:
        missing.append("sandbox.allowUnsandboxedCommands must be false")
    if not sandbox.get("network", {}).get("allowedDomains"):
        missing.append("sandbox.network.allowedDomains must be non-empty")
    if not sandbox.get("filesystem", {}).get("denyRead"):
        missing.append("sandbox.filesystem.denyRead must be non-empty")
    return missing


def forge_toml_missing_entrypoints(forge_toml_path: Path) -> set[str]:
    """Return the subset of CONTRACTS.md §9's registered entrypoints that
    ``forge.toml`` does not reference in any [[verify]] block."""
    data = tomllib.loads(Path(forge_toml_path).read_text(encoding="utf-8"))
    found: set[str] = set()
    for block in data.get("verify", []):
        found.update(block.get("entrypoints", []))
    return REQUIRED_VERIFY_ENTRYPOINTS - found
