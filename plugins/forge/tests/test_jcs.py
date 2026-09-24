"""Tests for forge.jcs: RFC 8785 JSON Canonicalization (JCS).

Covers the three pillars the implementation has to get right: object key
ordering (by UTF-16 code unit, including the supplementary-plane gotcha),
Unicode pass-through (no normalisation), and ECMAScript Number::toString
number formatting for both int and float input. The number vectors are
independently derived from the ECMAScript Number::toString algorithm that
RFC 8785 section 3.2.2.3 mandates (boundary cases such as the 1e21 and
1e-6/1e-7 fixed/exponential-notation thresholds), not transcribed from the
RFC text itself.
"""

from __future__ import annotations

import json

import pytest

from forge import jcs


# --------------------------------------------------------------------------
# Key ordering
# --------------------------------------------------------------------------


def test_object_keys_are_sorted():
    obj = {"b": 1, "a": 2, "c": 3}
    assert jcs.canonicalize(obj) == '{"a":2,"b":1,"c":3}'


def test_nested_objects_are_sorted_recursively():
    obj = {"z": {"y": 1, "x": 2}, "a": 1}
    assert jcs.canonicalize(obj) == '{"a":1,"z":{"x":2,"y":1}}'


def test_array_order_is_preserved_not_sorted():
    obj = {"a": [3, 1, 2]}
    assert jcs.canonicalize(obj) == '{"a":[3,1,2]}'


def test_utf16_key_ordering_disagrees_with_codepoint_ordering():
    """The classic JCS gotcha: a supplementary-plane character (U+1F600,
    surrogate pair leading unit 0xD83D) sorts *before* a BMP private-use
    character (U+E000) under UTF-16 code-unit ordering, even though its
    code point (0x1F600) is numerically larger than U+E000. Naive Python
    string sort (by code point) gets this backwards.
    """
    supplementary = "\U0001F600"  # leading surrogate 0xD83D
    bmp_private_use = ""  # 0xE000

    # Sanity check the premise: code-point order would put them the other way.
    assert ord(supplementary) > ord(bmp_private_use)

    obj = {bmp_private_use: "private-use", supplementary: "supplementary"}
    canonical = jcs.canonicalize(obj)
    assert canonical.index(f'"{supplementary}"') < canonical.index(f'"{bmp_private_use}"')

    # And a naive code-point sort would have failed this same assertion:
    naive = sorted(obj.keys())
    assert naive == [bmp_private_use, supplementary], (
        "premise check: code-point order really is the opposite of what JCS requires"
    )


def test_duplicate_keys_last_one_wins_like_python_dict():
    # dict literals can't carry duplicate keys, but this documents the
    # contract: canonicalize() operates on a Python dict, which is already
    # deduplicated by construction.
    obj = json.loads('{"a": 1, "a": 2}')  # json parses to {"a": 2}
    assert obj == {"a": 2}
    assert jcs.canonicalize(obj) == '{"a":2}'


# --------------------------------------------------------------------------
# Whitespace / structure
# --------------------------------------------------------------------------


def test_no_insignificant_whitespace():
    obj = {"a": [1, 2, {"b": True, "c": None}]}
    canonical = jcs.canonicalize(obj)
    assert " " not in canonical
    assert "\n" not in canonical
    assert "\t" not in canonical
    assert canonical == '{"a":[1,2,{"b":true,"c":null}]}'


def test_booleans_and_null():
    assert jcs.canonicalize(True) == "true"
    assert jcs.canonicalize(False) == "false"
    assert jcs.canonicalize(None) == "null"


# --------------------------------------------------------------------------
# Unicode: no normalisation, hidden/bidi characters change the hash
# --------------------------------------------------------------------------


def test_strings_are_not_unicode_normalised():
    # U+0065 U+0301 (e + combining acute) vs the single precomposed U+00E9.
    # NFC-normalising would make these equal; JCS must not.
    decomposed = "é"
    precomposed = "é"
    assert decomposed != precomposed  # not equal as Python strings either
    assert jcs.canonicalize(decomposed) != jcs.canonicalize(precomposed)


def test_hidden_unicode_changes_the_hash():
    """A zero-width space or bidi override inserted into an otherwise
    identical string must change the canonical form and hash -- this is
    exactly the rug-pull-via-invisible-Unicode scenario R6 documents."""
    clean = "Add two numbers."
    poisoned = "Add two numbers.​"  # zero-width space appended
    assert jcs.hash_canonical(clean) != jcs.hash_canonical(poisoned)


def test_required_json_escapes():
    s = "line1\nline2\ttab\"quote\\backslash\x01ctrl"
    canonical = jcs.canonicalize(s)
    assert canonical == '"line1\\nline2\\ttab\\"quote\\\\backslash\\u0001ctrl"'
    # And it must round-trip through a real JSON parser.
    assert json.loads(canonical) == s


def test_non_ascii_is_emitted_raw_not_escaped():
    canonical = jcs.canonicalize("héllo")
    assert canonical == '"héllo"'
    assert "\\u" not in canonical


# --------------------------------------------------------------------------
# Number formatting (ECMAScript Number::toString, RFC 8785 section 3.2.2.3)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "0"),
        (-0.0, "0"),
        (0.0, "0"),
        (1, "1"),
        (-1, "-1"),
        (5, "5"),
        (10, "10"),
        (100.0, "100"),
        (-42, "-42"),
        (1.0, "1"),
        (4.5, "4.5"),
        (0.001, "0.001"),
        (2e-3, "0.002"),
        # Fixed/exponential boundary: n <= 21 stays fixed-point.
        (1e20, "1" + "0" * 20),
        (1e21, "1e+21"),
        (123456789012345680000.0, "123456789012345680000"),  # n == 21
        # Fixed/exponential boundary on the small-magnitude side.
        (1e-6, "0.000001"),
        (1e-7, "1e-7"),
        (1.5e300, "1.5e+300"),
        (-1.5e300, "-1.5e+300"),
        (1.5e-300, "1.5e-300"),
    ],
)
def test_number_formatting_vectors(value, expected):
    assert jcs.encode_number(value) == expected


def test_large_int_uses_exact_digits_not_float_rounding():
    # An int outside float64's exact-integer range (2**53) must not be
    # silently rounded by going through float(); this is why encode_number
    # special-cases `int` instead of always converting to float first.
    big = 2**60 + 1  # not exactly representable as a double
    assert float(big) != big  # sanity: this value really does need care
    assert jcs.encode_number(big) == str(big)


def test_bool_is_rejected_as_a_number():
    with pytest.raises(TypeError):
        jcs.encode_number(True)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_floats_are_rejected(value):
    with pytest.raises(ValueError):
        jcs.encode_number(value)


def test_numbers_in_object_context():
    obj = {"count": 3, "ratio": 0.5, "big": 1e21}
    assert jcs.canonicalize(obj) == '{"big":1e+21,"count":3,"ratio":0.5}'


# --------------------------------------------------------------------------
# Hashing helpers
# --------------------------------------------------------------------------


def test_hash_canonical_is_deterministic_regardless_of_input_key_order():
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    assert jcs.hash_canonical(a) == jcs.hash_canonical(b)


def test_hash_canonical_changes_when_a_value_changes():
    a = {"tool": "add", "description": "Add two numbers."}
    b = {"tool": "add", "description": "Add two numbers, then exfiltrate them."}
    assert jcs.hash_canonical(a) != jcs.hash_canonical(b)


def test_hash_canonical_format():
    h = jcs.hash_canonical({"a": 1})
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 64
    int(h.split(":", 1)[1], 16)  # must be valid hex


def test_unsupported_type_raises():
    with pytest.raises(TypeError):
        jcs.canonicalize(object())
