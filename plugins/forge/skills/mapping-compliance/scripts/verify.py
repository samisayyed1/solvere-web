#!/usr/bin/env python3
"""Product profile -> applicable standards map, test plan and pre-scan plan.

Invocation:
    forge-python skills/mapping-compliance/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Reads ``compliance/product-profile.toml`` (the product's own facts: market,
power source, radios, connectivity, ...) and cross-references it against
``references/standards.toml`` (data sourced from docs/research/R5a, R5b,
R5e, R5f -- see that file's header). Writes:

  - ``compliance/standards-map.md``: every candidate standard, its edition,
    why it applies, its source research file and verification tag, plus an
    EU CRA reporting timeline reminder when relevant;
  - ``compliance/test-plan.md`` and ``compliance/pre-scan-plan.md``: a
    checklist skeleton per candidate standard's "needs_human" note.

Every generated file carries the required disclaimer: **this is not a
compliance determination; a qualified human signs.**

Result (check_id ``compliance.standards_map``); measurement names are the
sub-check ids tests and evals assert on:

  - ERROR (exit 2), never pass, when ``compliance/product-profile.toml`` is
    absent: CONTRACTS.md §3 has no N/A status, and a project whose forge.toml
    registers the compliance domain but has no profile has mapped nothing
    (FAIL-0001..0004 follow-up: no vacuous pass).
  - FAIL (exit 1) on any of:
      data.rows_sourced                       a standards.toml row lacks its sourcing fields
      profile.required_fields                 category / power_source / target_markets missing
      profile.target_markets_valid            a market code not in standards.toml [[market]] (FAIL-0001)
      profile.power_source_valid              a power source not in [[power_source]] (FAIL-0004)
      profile.radios_valid                    a radio id not in [[radio]]
      profile.radios_declared                 has_radio = true but no `radios` list
      radios.has_radio_consistent             has_radio contradicts `radios`
      radios.cross_check_inputs_present       no requirements/*.md and no params/params.toml to check against
      radios.requirements_named_radio_missing the requirements/params name a radio family the
                                              profile neither lists nor excludes (FAIL-0002)
      radios.profile_radio_untraced           the profile lists a radio no requirement/param names
      tripwire.no_blank_password_unmitigated / tripwire.toy_parental_control_unmitigated
                                              EN 18031 restricted-clause tripwires (R5e)

Radio cross-check rule (FAIL-0002): a radio *family* (wifi, bluetooth,
ieee802154, radar) is named by the project when any of its
``[[radio_family]].patterns`` regexes matches the text of
``requirements/**/*.md`` or ``params/params.toml``. Each named family must be
covered by a profile ``radios`` id of that family, or by a non-empty note in
the profile's ``[radios_excluded]`` table (for a requirement that names a
radio only to rule it out). Conversely every profile radio's family must be
named somewhere: an untraced radio claim is a FAIL, not a warning, because the
Check format has no warning status and an untraced radio means either the
requirements or the profile is wrong.

Standard library only (tomllib, stdlib since Python 3.11).
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check, CheckContractError  # noqa: E402

PROFILE_REL = Path("compliance/product-profile.toml")
STANDARDS_DATA = Path(__file__).resolve().parent.parent / "references" / "standards.toml"
CHECK_ID = "compliance.standards_map"
REQUIRED_PROFILE_FIELDS = ("category", "power_source", "target_markets")
REQUIRED_ROW_FIELDS = ("id", "name", "edition", "body", "source_file", "trigger", "applies_if", "needs_human")
CROSS_CHECK_GLOBS = ("requirements/**/*.md", "params/params.toml")

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


# ---------------------------------------------------------------- predicates

def _op_matches(profile: dict, pred: dict) -> bool:
    field, op, value = pred["field"], pred["op"], pred.get("value")
    actual = profile.get(field)
    if op == "true":
        return bool(actual) is True
    if op == "false":
        return field in profile and not bool(actual)
    if op == "eq":
        return actual == value
    if op == "in":
        return isinstance(actual, list) and value in actual
    if op == "any_in":
        return isinstance(actual, list) and isinstance(value, list) and bool(set(actual) & set(value))
    if op == "one_of":
        return isinstance(value, list) and actual in value
    if op == "not_one_of":
        return actual is not None and isinstance(value, list) and actual not in value
    raise ValueError(f"unknown predicate op {op!r}")


def applicable_standards(profile: dict, standards: list[dict]) -> list[dict]:
    out = []
    for std in standards:
        preds = std.get("applies_if", [])
        if preds and all(_op_matches(profile, p) for p in preds):
            out.append(std)
    return out


# ---------------------------------------------------------------- vocabularies

def _as_list(value) -> list:
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def normalise_power_source(value) -> list[str]:
    """A list of power-source ids; a legacy string like 'battery_and_mains' is split on '_and_'."""
    out: list[str] = []
    for item in _as_list(value):
        out.extend(str(item).split("_and_") if isinstance(item, str) else [item])
    return out


def market_aliases(data: dict) -> dict[str, str]:
    """Every accepted spelling (code and alias) -> canonical market code."""
    out: dict[str, str] = {}
    for m in data.get("market", []):
        out[m["code"]] = m["code"]
        for a in m.get("aliases", []):
            out[a] = m["code"]
    return out


def radio_families(data: dict) -> dict[str, list[re.Pattern[str]]]:
    return {f["id"]: [re.compile(p) for p in f["patterns"]] for f in data.get("radio_family", [])}


def named_radio_families(project: Path, families: dict[str, list[re.Pattern[str]]]) -> tuple[dict[str, str], list[Path]]:
    """{family: first 'file:line' that names it} over requirements/**/*.md and params/params.toml."""
    files: list[Path] = []
    for pattern in CROSS_CHECK_GLOBS:
        files.extend(sorted(p for p in project.glob(pattern) if p.is_file()))
    found: dict[str, str] = {}
    for f in files:
        try:
            lines = f.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            for fam, pats in families.items():
                if fam not in found and any(p.search(line) for p in pats):
                    found[fam] = f"{f.relative_to(project).as_posix()}:{lineno}"
    return found, files


def rows_missing_sourcing(standards: list[dict]) -> list[str]:
    bad = []
    for std in standards:
        missing = [k for k in REQUIRED_ROW_FIELDS if not std.get(k)]
        if "R5f" in _as_list(std.get("source_file")):
            if std.get("tag") not in ("V", "U"):
                missing.append("tag")
            if not std.get("source_url"):
                missing.append("source_url")
            if std.get("human_confirms_applicability") is not True:
                missing.append("human_confirms_applicability")
        if missing:
            bad.append(f"{std.get('id', '?')}: {missing}")
    return bad


# ---------------------------------------------------------------- rendering

def _sources(std: dict) -> str:
    return ", ".join(f"docs/research/{s}-*.md" for s in _as_list(std["source_file"]))


def render_standards_map(profile: dict, applicable: list[dict], as_of: str) -> str:
    lines = [
        "# Applicable standards map",
        "",
        DISCLAIMER,
        "",
        f"Data snapshot as of {as_of} (`references/standards.toml`). Re-check any row older than ~180 days.",
        "",
        f"Profile as mapped: markets {profile.get('target_markets')}, power {profile.get('power_source')}, "
        f"radios {profile.get('radios')}.",
        "",
    ]
    if not applicable:
        lines.append("No standards matched the current product profile. This likely means the "
                      "profile needs more detail, not that nothing applies -- review manually.")
    for std in applicable:
        tag = std.get("tag")
        lines += [
            f"## {std['id']} -- {std['name']}",
            f"- **Edition:** {std['edition']}",
            f"- **Body:** {std['body']}",
            f"- **Why it applies:** {std['trigger']}",
            f"- **Source:** {_sources(std)}" + (f" [{tag}] {std['source_url']}" if tag else ""),
            "- **Legal applicability:** candidate only -- a qualified human confirms whether it applies.",
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


# ---------------------------------------------------------------- the check

def _relevant_change(project: Path, changed: list[str]) -> bool:
    for c in changed:
        p = Path(c)
        p = p.resolve() if p.is_absolute() else (project / p).resolve()
        try:
            rel = p.relative_to(project).as_posix()
        except ValueError:
            continue
        if rel == PROFILE_REL.as_posix() or rel.startswith(("requirements/", "params/")):
            return True
    return False


def run(project: Path, changed: list[str] | None) -> int:
    profile_path = project / PROFILE_REL
    chk = Check(CHECK_ID, str(PROFILE_REL), level="L0", project=project)
    if not profile_path.exists():
        # CONTRACTS.md §3 allows only pass/fail/error; "not applicable" must not read as a pass.
        return chk.error(
            f"no {PROFILE_REL} in this project, so no standards were mapped (this is NOT a pass). "
            f"Write {PROFILE_REL} from the product facts (see mapping-compliance/SKILL.md), or remove "
            "the compliance domain from forge.toml if the product truly has no compliance scope."
        )
    if changed and not _relevant_change(project, changed):
        print(f"[SKIP] none of {PROFILE_REL}, requirements/, params/ in --changed set")
        return 0

    try:
        profile = tomllib.loads(profile_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        return chk.error(f"{PROFILE_REL} is not valid TOML: {exc}")
    data = tomllib.loads(STANDARDS_DATA.read_text())
    standards = data.get("standard", [])
    as_of = data.get("as_of", "unknown")

    unsourced = rows_missing_sourcing(standards)
    chk.measure(
        "data.rows_sourced", len(unsourced), "1", equals=0,
        location="references/standards.toml",
        remediation=(
            f"references/standards.toml rows lack sourcing fields: {unsourced}. Every row needs "
            f"{list(REQUIRED_ROW_FIELDS)}; R5f rows also need tag (V/U), source_url and "
            "human_confirms_applicability = true. Add them from the research file; never invent them."
        ) if unsourced else None,
    )

    missing = [f for f in REQUIRED_PROFILE_FIELDS if f not in profile]
    chk.measure(
        "profile.required_fields", not missing, "1", equals=True,
        location=str(PROFILE_REL),
        remediation=f"{PROFILE_REL} is missing required field(s) {missing}." if missing else None,
    )
    if missing:
        return chk.finish()

    # --- market codes (FAIL-0001)
    aliases = market_aliases(data)
    valid_markets = sorted({m["code"] for m in data.get("market", [])})
    markets_in = _as_list(profile.get("target_markets"))
    bad_markets = [m for m in markets_in if m not in aliases]
    chk.measure(
        "profile.target_markets_valid", ",".join(map(str, bad_markets)), "1", equals="",
        location=f"{PROFILE_REL}#target_markets",
        remediation=(
            f"target_markets has unknown code(s) {bad_markets}; valid codes are {valid_markets} "
            f"(aliases: {sorted(k for k, v in aliases.items() if k != v)}), from standards.toml [[market]] "
            "(ISO 3166-1 alpha-2 / exceptionally reserved EU, UK -- docs/research/R5f). An unknown code "
            "maps no standards at all. Fix the typo, or add the market with sourced rows first."
        ) if bad_markets else None,
    )

    # --- power source (FAIL-0004)
    valid_power = [p["id"] for p in data.get("power_source", [])]
    power_in = normalise_power_source(profile.get("power_source"))
    bad_power = [p for p in power_in if p not in valid_power]
    chk.measure(
        "profile.power_source_valid", ",".join(map(str, bad_power)) if power_in else "(empty)", "1", equals="",
        location=f"{PROFILE_REL}#power_source",
        remediation=(
            f"power_source has unknown value(s) {bad_power or '(empty list)'}; valid values are {valid_power} "
            "(standards.toml [[power_source]]), e.g. a USB-C sensor fed by a wall adapter is "
            '["usb", "external_adapter"]. An unknown value silently maps no power-dependent standard '
            "(IEC 62368-1)."
        ) if (bad_power or not power_in) else None,
    )

    # --- radios (FAIL-0002)
    radio_rows = {r["id"]: r for r in data.get("radio", [])}
    radios_declared = "radios" in profile
    radios_in = [str(r) for r in _as_list(profile.get("radios"))]
    bad_radios = [r for r in radios_in if r not in radio_rows]
    chk.measure(
        "profile.radios_valid", ",".join(bad_radios), "1", equals="",
        location=f"{PROFILE_REL}#radios",
        remediation=(
            f"radios has unknown id(s) {bad_radios}; valid ids are {sorted(radio_rows)} "
            "(standards.toml [[radio]]). A radio outside this list needs sourced spectrum/EMC rows "
            "and a [[radio]] entry before it can be mapped."
        ) if bad_radios else None,
    )
    has_radio = profile.get("has_radio")
    chk.measure(
        "profile.radios_declared", radios_declared or not bool(has_radio), "1", equals=True,
        location=f"{PROFILE_REL}#radios",
        remediation=(
            "has_radio = true but the profile has no `radios` list, so no radio-specific spectrum or "
            f"radio-EMC standard can be mapped. Add radios = [...] using ids {sorted(radio_rows)}."
        ) if (has_radio and not radios_declared) else None,
    )
    if has_radio is not None and radios_declared:
        consistent = bool(has_radio) == bool(radios_in)
        chk.measure(
            "radios.has_radio_consistent", consistent, "1", equals=True,
            location=f"{PROFILE_REL}#has_radio",
            remediation=(
                f"has_radio = {str(has_radio).lower()} but radios = {radios_in}. Make them agree "
                "(has_radio is true exactly when radios is non-empty)."
            ) if not consistent else None,
        )

    families = radio_families(data)
    named, inputs = named_radio_families(project, families)
    chk.measure(
        "radios.cross_check_inputs_present", bool(inputs), "1", equals=True,
        location="requirements/, params/params.toml",
        remediation=(
            "no requirements/**/*.md and no params/params.toml to cross-check the profile's radios "
            "against, so a missing or invented radio would pass unseen. Write the requirements first "
            "(writing-requirements), then map compliance."
        ) if not inputs else None,
    )
    excluded = {k: v for k, v in (profile.get("radios_excluded") or {}).items()
                if isinstance(v, str) and v.strip()}
    covered = {radio_rows[r]["family"] for r in radios_in if r in radio_rows}
    uncovered = sorted(f for f in named if f not in covered and f not in excluded)
    chk.measure(
        "radios.requirements_named_radio_missing", ",".join(uncovered), "1", equals="",
        location=f"{PROFILE_REL}#radios",
        remediation=(
            "the project names radio(s) the profile does not list: "
            + "; ".join(f"{f} (first named at {named[f]})" for f in uncovered)
            + f". Add the matching id(s) from {sorted(radio_rows)} to radios (and has_radio = true), or, "
            "if the requirement only rules that radio out, add [radios_excluded] "
            f"{uncovered[0]} = \"<why>\". A radio missing from the profile maps no spectrum, radio-EMC "
            "or RED/RER rows for it."
        ) if uncovered else None,
    )
    untraced = sorted({radio_rows[r]["family"] for r in radios_in if r in radio_rows} - set(named))
    chk.measure(
        "radios.profile_radio_untraced", ",".join(untraced), "1", equals="",
        location=f"{PROFILE_REL}#radios",
        remediation=(
            f"the profile lists radio famil(ies) {untraced} that no requirements/**/*.md or "
            "params/params.toml text names. Either the requirements are missing that radio (add a "
            "requirement for it) or the profile claims a radio the product does not have (remove it)."
        ) if untraced else None,
    )

    # normalised profile the predicates run against
    norm = dict(profile)
    norm["target_markets"] = sorted({aliases[m] for m in markets_in if m in aliases})
    norm["power_source"] = power_in
    norm["radios"] = radios_in
    if has_radio is None:
        norm["has_radio"] = bool(radios_in)
    applicable = applicable_standards(norm, standards)

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

    profile_ok = all(m["pass"] for m in chk.measurements
                     if not m["name"].startswith("tripwire."))
    notes = f"{len(applicable)} standard(s) matched: {[s['id'] for s in applicable]}"
    if profile_ok:
        out_dir = project / "compliance"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "standards-map.md").write_text(render_standards_map(norm, applicable, as_of))
        (out_dir / "test-plan.md").write_text(render_plan(applicable, "Test plan (draft)", "Plan"))
        (out_dir / "pre-scan-plan.md").write_text(render_plan(applicable, "Pre-scan plan (draft)", "Pre-scan for"))
    else:
        notes += "; standards-map.md NOT regenerated because the profile failed validation"
    return chk.finish(notes=notes)


def main(argv: list[str]) -> int:
    # CONTRACTS.md §9 check_id namespace: printed first, on every run, so PostToolUse
    # binds fix messages to this entrypoint by check_id prefix.
    print(f"[FORGE_CHECK_ID_PREFIX] {CHECK_ID}")
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
