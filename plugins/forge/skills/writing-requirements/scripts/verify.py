#!/usr/bin/env python3
"""EARS lint over requirements/requirements.md (CONTRACTS.md §6, §9).

Invocation (CONTRACTS §9):
    forge-python skills/writing-requirements/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Checks, one measurement per requirement per rule, all under check_id
``requirements.ears_lint``:
  - ID format REQ-<AREA>-<NNN> (NNN >= 3 digits) and uniqueness across the file
  - exactly one EARS pattern per requirement (exactly one "shall", and the
    sentence matches one of the six EARS templates)
  - a ``Rationale:`` line and a ``Verify:`` line are present
  - ``Verify:`` is one of inspection, analysis, demo, test
  - no vague words (fast, user-friendly, approximately, etc., and/or, ...)
  - no bare numbers without a unit token next to them

Standard library only. Exits 0 (all requirements pass), 1 (a rule failed),
2 (nothing to check, or an internal error -- never printed as a pass).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check, CheckContractError  # noqa: E402

REQUIREMENTS_REL = Path("requirements/requirements.md")
CHECK_ID = "requirements.ears_lint"

ID_RE = re.compile(r"^REQ-([A-Z]+)-(\d{3,})$")
# Loose on purpose: any heading that *looks* like a requirement ID (starts
# with "REQ-") is captured as a requirement block, even if the ID itself is
# malformed (lowercase area, too few digits, ...). The strict ID_RE check
# below then fails it explicitly instead of the heading being silently
# dropped from parsing, which used to end in a false "no requirements found"
# SKIP (S2, phase3-review-2-addendum-sweep.md).
HEADING_RE = re.compile(r"^#{1,6}\s+(REQ-\S*)\s*$")
RATIONALE_RE = re.compile(r"^Rationale:\s*(.*)$", re.IGNORECASE)
VERIFY_RE = re.compile(r"^Verify:\s*(.*)$", re.IGNORECASE)
VALID_VERIFY = {"inspection", "analysis", "demo", "test"}

# The six EARS templates (Mavin et al., RE'09; see R5b). One requirement
# matches at least one of these leading-clause shapes and ends in "shall".
EARS_PATTERNS = {
    "ubiquitous": re.compile(r"^The\s+\S.*\bshall\b", re.IGNORECASE),
    "event": re.compile(r"^When\s+\S.*,\s*(the\s+)?\S.*\bshall\b", re.IGNORECASE),
    "state": re.compile(r"^While\s+\S.*,\s*(the\s+)?\S.*\bshall\b", re.IGNORECASE),
    "unwanted": re.compile(r"^If\s+\S.*,\s*then\s+(the\s+)?\S.*\bshall\b", re.IGNORECASE),
    "optional": re.compile(r"^Where\s+\S.*,\s*(the\s+)?\S.*\bshall\b", re.IGNORECASE),
    "complex": re.compile(
        r"^(While|When)\s+\S.*,\s*(when|where)\s+\S.*,\s*(the\s+)?\S.*\bshall\b",
        re.IGNORECASE,
    ),
}

VAGUE_WORDS = [
    "fast", "quickly", "quick", "user-friendly", "user friendly", "approximately",
    "etc.", "etc", "and/or", "easy to use", "intuitive", "robust", "seamless",
    "seamlessly", "efficient", "efficiently", "appropriate", "adequate",
    "as needed", "as required", "tbd", "several", "many", "some", "reasonable",
    "minimal", "maximal", "optimal", "flexible", "scalable", "simple",
]

# Units recognised immediately after a number (SI + common engineering units).
# "c" is accepted bare, alongside "°c"/"degc": Celsius is routinely typed
# without the degree sign, and a real typo (e.g. "gg", "mmm") still won't
# match any alternative here (S2 eval defect).
UNIT_RE = re.compile(
    r"^(mm|cm|m|km|mm2|mm3|cm2|cm3|m2|m3|in|ft|mil|"
    r"g|kg|mg|lb|lbs|oz|"
    r"s|ms|us|µs|min|hr|hrs|h|"
    r"v|mv|kv|a|ma|ua|µa|w|mw|kw|"
    r"hz|khz|mhz|ghz|"
    r"n|nm|kn|pa|kpa|mpa|bar|psi|"
    r"°c|°f|c|k|degc|degf|"
    r"%|ppm|db|dbm|"
    r"bit|bits|byte|bytes|kb|mb|gb|"
    r"lm|"
    r"cycles|times|x)\.?,?$",
    re.IGNORECASE,
)
# A bare number is one NOT immediately followed by a recognised unit word,
# and not part of a REQ-ID, a section number, or a list marker.
NUMBER_RE = re.compile(r"(?<![\w.-])(\d+(?:\.\d+)?)(?!\d)")

# Standards-body prefixes: the number right after one of these (e.g. "IEC
# 60529", "EN 301 489-1") is a standard designation, not a bare quantity, so
# it is exempt from the units check (S2 eval defect: EARS false positives).
STANDARD_PREFIXES = {
    "iec", "iso", "en", "ieee", "ansi", "ul", "astm", "din", "nema",
    "jedec", "etsi", "fcc", "cispr", "mil-std", "mil", "bs", "csa", "rohs",
}


class Requirement:
    __slots__ = ("req_id", "line_no", "sentence", "rationale", "verify")

    def __init__(self, req_id: str, line_no: int) -> None:
        self.req_id = req_id
        self.line_no = line_no
        self.sentence = ""
        self.rationale: str | None = None
        self.verify: str | None = None


def parse_requirements(text: str) -> list[Requirement]:
    lines = text.splitlines()
    reqs: list[Requirement] = []
    current: Requirement | None = None
    sentence_lines: list[str] = []

    def flush_sentence() -> None:
        if current is not None:
            current.sentence = " ".join(sentence_lines).strip()

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        heading = HEADING_RE.match(line)
        if heading:
            flush_sentence()
            current = Requirement(heading.group(1), i)
            reqs.append(current)
            sentence_lines = []
            continue
        if current is None:
            continue
        rationale = RATIONALE_RE.match(line)
        if rationale:
            flush_sentence()
            current.rationale = rationale.group(1).strip()
            continue
        verify = VERIFY_RE.match(line)
        if verify:
            current.verify = verify.group(1).strip().lower()
            continue
        if line.strip() and current.rationale is None:
            sentence_lines.append(line.strip())
    flush_sentence()
    return reqs


def _flag_vague_words(sentence: str) -> list[str]:
    low = sentence.lower()
    return [w for w in VAGUE_WORDS if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", low)]


def _flag_bare_numbers(sentence: str) -> list[str]:
    bad: list[str] = []
    tokens = sentence.split()
    for idx, tok in enumerate(tokens):
        m = NUMBER_RE.fullmatch(tok.strip(".,;:()"))
        if not m:
            # number glued to a unit already, e.g. "2.0mm" -- fine
            continue
        prev = tokens[idx - 1].strip(".,;:()") if idx > 0 else ""
        if prev.lower() in STANDARD_PREFIXES:
            # a standard designation ("IEC 60529", "EN 301 489-1"), not a
            # quantity that needs a unit
            continue
        nxt = tokens[idx + 1] if idx + 1 < len(tokens) else ""
        nxt_clean = nxt.strip(".,;:()")
        if UNIT_RE.match(nxt_clean):
            continue
        bad.append(tok)
    return bad


# Phrases that establish a lower or upper numeric bound in a requirement
# sentence, so a min above its max can be flagged (S2: "at least 300 g and
# at most 200 g" used to pass silently).
LOWER_BOUND_RE = re.compile(
    r"(?:at least|no less than|a minimum of|minimum of)\s+([\d.]+)", re.IGNORECASE
)
UPPER_BOUND_RE = re.compile(
    r"(?:at most|no more than|a maximum of|maximum of)\s+([\d.]+)", re.IGNORECASE
)


def _flag_bound_contradiction(sentence: str) -> tuple[float, float] | None:
    """Return (min, max) if the sentence's stated lower bound exceeds its
    stated upper bound, else None. Deliberately simple: it does not try to
    match units across the two bounds, since a contradictory pair is wrong
    regardless of whether the units match."""
    lowers = [float(x) for x in LOWER_BOUND_RE.findall(sentence)]
    uppers = [float(x) for x in UPPER_BOUND_RE.findall(sentence)]
    if not lowers or not uppers:
        return None
    worst_min, worst_max = max(lowers), min(uppers)
    if worst_min > worst_max:
        return worst_min, worst_max
    return None


def _matches_ears(sentence: str) -> str | None:
    for name, pattern in EARS_PATTERNS.items():
        if pattern.match(sentence):
            return name
    return None


def run(project: Path, changed: list[str] | None) -> int:
    req_path = project / REQUIREMENTS_REL
    if not req_path.exists():
        print(f"[SKIP] no {REQUIREMENTS_REL} in this project")
        return 0
    if changed and not any(Path(c).resolve() == req_path.resolve() for c in changed):
        print(f"[SKIP] {REQUIREMENTS_REL} not in --changed set")
        return 0

    text = req_path.read_text()
    reqs = parse_requirements(text)
    chk = Check(CHECK_ID, str(REQUIREMENTS_REL), level="L1", project=project)

    if not reqs:
        # Nothing to check is a SKIP per CONTRACTS §9, not a pass or fail.
        print(f"[SKIP] no requirements found in {REQUIREMENTS_REL}")
        return 0

    seen_ids: dict[str, int] = {}
    for req in reqs:
        loc = f"{REQUIREMENTS_REL}:{req.line_no}"
        # Disambiguate measurement names by line: a duplicate-ID requirement
        # would otherwise collide with the first block's measurement names,
        # hiding the duplicate's own findings under the same JSON key.
        mkey = f"{req.req_id}@L{req.line_no}"

        id_match = ID_RE.match(req.req_id)
        chk.measure(
            f"{mkey}.id_format", id_match is not None, "1", equals=True,
            requirement=req.req_id if id_match else None, location=loc,
            remediation=(
                f"{req.req_id} does not match REQ-<AREA>-<NNN> (area uppercase letters, "
                "at least 3 digits). Rename it to match, e.g. REQ-MECH-004."
            ) if not id_match else None,
        )

        dup = req.req_id in seen_ids
        chk.measure(
            f"{mkey}.unique_id", not dup, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} is reused (first seen at line {seen_ids.get(req.req_id)}). "
                "Every requirement ID must be unique in the file."
            ) if dup else None,
        )
        seen_ids.setdefault(req.req_id, req.line_no)

        shall_count = len(re.findall(r"\bshall\b", req.sentence, re.IGNORECASE))
        one_shall = shall_count == 1
        chk.measure(
            f"{mkey}.one_shall", one_shall, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} has {shall_count} 'shall' clauses; split it into "
                "separate requirements, one 'shall' each."
            ) if not one_shall else None,
        )

        pattern = _matches_ears(req.sentence) if req.sentence else None
        matched = pattern is not None
        chk.measure(
            f"{mkey}.ears_pattern", matched, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} does not match a recognised EARS pattern "
                "(ubiquitous/event/state/unwanted/optional/complex). "
                f"Sentence: {req.sentence!r}. Rewrite starting with The/When/While/If/Where."
            ) if not matched else None,
        )

        has_rationale = bool(req.rationale)
        chk.measure(
            f"{mkey}.has_rationale", has_rationale, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} is missing a 'Rationale:' line explaining why it exists."
            ) if not has_rationale else None,
        )

        has_verify_line = req.verify is not None
        chk.measure(
            f"{mkey}.has_verify_line", has_verify_line, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} is missing a 'Verify:' line."
            ) if not has_verify_line else None,
        )
        if has_verify_line:
            valid_verify = req.verify in VALID_VERIFY
            chk.measure(
                f"{mkey}.verify_method", valid_verify, "1", equals=True, location=loc,
                remediation=(
                    f"{req.req_id} Verify: {req.verify!r} is not one of "
                    f"{sorted(VALID_VERIFY)}."
                ) if not valid_verify else None,
            )

        vague = _flag_vague_words(req.sentence)
        chk.measure(
            f"{mkey}.no_vague_words", not vague, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} uses vague word(s) {vague}: {req.sentence!r}. "
                "Replace with a measurable, testable criterion."
            ) if vague else None,
        )

        bare = _flag_bare_numbers(req.sentence)
        chk.measure(
            f"{mkey}.numbers_have_units", not bare, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} has number(s) without a unit: {bare} in {req.sentence!r}. "
                "Every number needs an explicit unit (use '1' for a unitless count)."
            ) if bare else None,
        )

        bound_issue = _flag_bound_contradiction(req.sentence)
        chk.measure(
            f"{mkey}.bounds_consistent", bound_issue is None, "1", equals=True, location=loc,
            remediation=(
                f"{req.req_id} requires at least {bound_issue[0]} and at most "
                f"{bound_issue[1] if bound_issue else ''}, which is contradictory "
                "(the minimum exceeds the maximum). Fix the bounds so min <= max."
            ) if bound_issue else None,
        )

    return chk.finish()


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print(f"[FORGE_CHECK_ID_PREFIX] {CHECK_ID}")
    project = Path(".")
    changed: list[str] = []
    fast = False
    i = 0
    while i < len(argv):
        if argv[i] == "--project":
            project = Path(argv[i + 1]); i += 2
        elif argv[i] == "--changed":
            changed.append(argv[i + 1]); i += 2
        elif argv[i] == "--fast":
            fast = True; i += 1
        else:
            i += 1
    del fast  # the lint is already well under 30s; no fast-path needed
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
