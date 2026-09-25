#!/usr/bin/env python3
"""Product profile -> applicable standards map, test plan and pre-scan plan.

Invocation:
    forge-python skills/mapping-compliance/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Reads ``compliance/product-profile.toml`` (the product's own facts: market,
power source, radio, connectivity, ...) and cross-references it against
``references/standards.toml`` (data sourced from docs/research/R5a, R5b,
R5e -- see that file's header). Writes:

  - ``compliance/standards-map.md``: every applicable standard, its edition,
    why it applies, and the source research file, plus an EU CRA reporting
    timeline reminder when relevant;
  - ``compliance/test-plan.md`` and ``compliance/pre-scan-plan.md``: a
    checklist skeleton per applicable standard's "needs_human" note.

Every generated file carries the required disclaimer: **this is not a
compliance determination; a qualified human signs.**

FAILS (check_id ``compliance.standards_map``) when:
  - the product profile is missing a required field;
  - an **EN 18031 restricted-clause tripwire** fires (a no-password mode, or
    toy/childcare radio equipment with no parental control) and the
    profile has no mitigation note -- these are the exact cases R5e says
    give *no* presumption of conformity, so they need a human decision,
    not silence.

Standard library only (tomllib, stdlib since Python 3.11).
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check, CheckContractError  # noqa: E402

PROFILE_REL = Path("compliance/product-profile.toml")
STANDARDS_DATA = Path(__file__).resolve().parent.parent / "references" / "standards.toml"
CHECK_ID = "compliance.standards_map"
REQUIRED_PROFILE_FIELDS = ("category", "power_source", "target_markets")

DISCLAIMER = (
    "**This is not a compliance determination.** It flags candidate standards and their "
    "sourced trigger reasons for a qualified human to review, scope and sign. Testing, "
    "certification and declarations of conformity always need an accredited lab, a notified "
    "body, or a named qualified person -- never Forge."
)

CRA_TIMELINE = """## EU Cyber Resilience Act reporting timeline (Regulation (EU) 2024/2847)

Source: docs/research/R5e-standards-materials-radio-security.md.

- **2024-12-10**: CRA in force.
- **2026-06-11**: rules for notified conformity-assessment bodies apply.
- **2026-09-11**: Article 14 reporting duties apply -- 24h early warning / 72h
  notification / final report within 14 days (vulnerability) or 1 month
  (incident), via ENISA's Single Reporting Platform. This covers products
  already on the market before full application.
- **2027-12-11**: full application (Annex I essential requirements, SBOM,
  CE marking, support-period declaration).

A named human submits every report. Forge only starts the clock and points
at the runbook -- it never files on anyone's behalf.
"""


def _op_matches(profile: dict, pred: dict) -> bool:
    field, op, value = pred["field"], pred["op"], pred.get("value")
    actual = profile.get(field)
    if op == "true":
        return bool(actual) is True
    if op == "eq":
        return actual == value
    if op == "in":
        return isinstance(actual, list) and value in actual
    raise ValueError(f"unknown predicate op {op!r}")


def applicable_standards(profile: dict, standards: list[dict]) -> list[dict]:
    out = []
    for std in standards:
        preds = std.get("applies_if", [])
        if preds and all(_op_matches(profile, p) for p in preds):
            out.append(std)
    return out


def render_standards_map(profile: dict, applicable: list[dict], as_of: str) -> str:
    lines = [
        "# Applicable standards map",
        "",
        DISCLAIMER,
        "",
        f"Data snapshot as of {as_of} (`references/standards.toml`). Re-check any row older than ~180 days.",
        "",
    ]
    if not applicable:
        lines.append("No standards matched the current product profile. This likely means the "
                      "profile needs more detail, not that nothing applies -- review manually.")
    for std in applicable:
        lines += [
            f"## {std['id']} -- {std['name']}",
            f"- **Edition:** {std['edition']}",
            f"- **Body:** {std['body']}",
            f"- **Why it applies:** {std['trigger']}",
            f"- **Source:** docs/research/{std['source_file']}-*.md",
            f"- **Needs a qualified human for:** {std.get('needs_human', '(see standard)')}",
            "",
        ]
    if any(s["id"] in ("eu-red-cyber", "eu-cra") for s in applicable):
        lines += ["", CRA_TIMELINE]
    return "\n".join(lines) + "\n"


def render_plan(applicable: list[dict], heading: str, verb: str) -> str:
    lines = [f"# {heading}", "", DISCLAIMER, ""]
    for std in applicable:
        lines += [f"## {std['id']}", f"- {verb}: {std.get('needs_human', '(see standard)')}", ""]
    return "\n".join(lines) + "\n"


def run(project: Path, changed: list[str] | None) -> int:
    profile_path = project / PROFILE_REL
    if not profile_path.exists():
        print(f"[SKIP] no {PROFILE_REL} in this project")
        return 0
    if changed and not any(Path(c).resolve() == profile_path.resolve() for c in changed):
        print(f"[SKIP] {PROFILE_REL} not in --changed set")
        return 0

    chk = Check(CHECK_ID, str(PROFILE_REL), level="L0", project=project)

    profile = tomllib.loads(profile_path.read_text())
    missing = [f for f in REQUIRED_PROFILE_FIELDS if f not in profile]
    all_present = not missing
    chk.measure(
        "profile.required_fields", all_present, "1", equals=True,
        remediation=(
            f"{PROFILE_REL} is missing required field(s) {missing}."
        ) if not all_present else None,
    )
    if not all_present:
        return chk.finish()

    data = tomllib.loads(STANDARDS_DATA.read_text())
    standards = data.get("standard", [])
    as_of = data.get("as_of", "unknown")
    applicable = applicable_standards(profile, standards)

    # EN 18031 restricted-clause tripwires (R5e): no presumption of conformity when --
    red_cyber_applies = any(s["id"] == "eu-red-cyber" for s in applicable)
    if red_cyber_applies:
        blank_pw = bool(profile.get("allows_blank_password"))
        pw_note = (profile.get("password_mitigation_note") or "").strip()
        chk.measure(
            "tripwire.no_blank_password_unmitigated", not blank_pw or bool(pw_note), "1", equals=True,
            remediation=(
                "profile.allows_blank_password is true -- EN 18031-1 clause 6.2.5.1/6.2.5.2 gives "
                "NO presumption of conformity when a user can skip setting a password. Either "
                "disallow the blank-password mode, or set 'password_mitigation_note' explaining "
                "the notified-body route (R5e)."
            ) if blank_pw and not pw_note else None,
        )

        is_toy = bool(profile.get("is_toy_or_childcare"))
        has_control = bool(profile.get("has_parental_control"))
        toy_note = (profile.get("toy_control_mitigation_note") or "").strip()
        chk.measure(
            "tripwire.toy_parental_control_unmitigated", not is_toy or has_control or bool(toy_note), "1",
            equals=True,
            remediation=(
                "profile.is_toy_or_childcare is true with radio internet connectivity but no "
                "parental/guardian control -- EN 18031-2 gives NO presumption of conformity in "
                "this case. Add parental control, or set 'toy_control_mitigation_note' (R5e)."
            ) if (is_toy and not has_control and not toy_note) else None,
        )

    out_dir = project / "compliance"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "standards-map.md").write_text(render_standards_map(profile, applicable, as_of))
    (out_dir / "test-plan.md").write_text(render_plan(applicable, "Test plan (draft)", "Plan"))
    (out_dir / "pre-scan-plan.md").write_text(render_plan(applicable, "Pre-scan plan (draft)", "Pre-scan for"))

    return chk.finish(notes=f"{len(applicable)} standard(s) matched: {[s['id'] for s in applicable]}")


def main(argv: list[str]) -> int:
    project = Path(".")
    changed: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--project":
            project = Path(argv[i + 1]); i += 2
        elif argv[i] == "--changed":
            changed.append(argv[i + 1]); i += 2
        elif argv[i] == "--fast":
            i += 1
        else:
            i += 1
    try:
        return run(project.resolve(), changed or None)
    except CheckContractError as exc:
        print(f"[ERROR] {CHECK_ID}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 -- fail closed
        print(f"[ERROR] {CHECK_ID}: internal error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
