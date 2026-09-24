"""RFC 8785 JSON Canonicalization Scheme (JCS).

Implements the three pillars of JCS:

1. Object members are ordered by sorting their names as sequences of
   **UTF-16 code units** (not Python's native code-point ordering, which
   disagrees with UTF-16 ordering for supplementary-plane characters).
2. No insignificant whitespace is emitted.
3. Numbers are serialised with the ECMAScript ``Number::toString`` (radix 10)
   algorithm from ECMA-262, which RFC 8785 mandates verbatim. This module
   implements that algorithm directly (not by delegating to a JS engine),
   for both ``int`` and ``float`` input, using the shortest round-tripping
   decimal digit string (the same guarantee Python's ``repr(float)`` makes)
   reshaped into the ECMAScript fixed/exponential layout rules.

Strings are re-emitted byte-for-byte aside from the mandatory JSON escapes
(quote, backslash, and control characters below U+0020). In particular this
module never Unicode-normalises: hidden or bidirectional control characters
(zero-width spaces, RTL overrides, etc.) change the canonical output and
therefore the hash, which is deliberate (see docs/research/R6, section 6).

Only JSON-representable Python values are accepted: ``dict`` (with ``str``
keys), ``list``/``tuple``, ``str``, ``bool``, ``int``, ``float`` and
``None``. NaN and Infinity are not valid JSON numbers and raise
``ValueError``.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

__all__ = [
    "canonicalize",
    "canonical_bytes",
    "sha256_hex",
    "hash_canonical",
    "encode_number",
]

_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}

_EXP_RE = re.compile(r"[eE]")


def canonicalize(value: Any) -> str:
    """Return the RFC 8785 canonical JSON text for ``value``."""
    return _encode_value(value)


def canonical_bytes(value: Any) -> bytes:
    """Return the canonical JSON text UTF-8 encoded, as RFC 8785 requires."""
    return canonicalize(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def hash_canonical(value: Any) -> str:
    """Return ``sha256:<hex>`` over the RFC 8785 canonical form of ``value``."""
    return "sha256:" + sha256_hex(canonical_bytes(value))


# --------------------------------------------------------------------------
# Value encoding
# --------------------------------------------------------------------------


def _encode_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):  # must precede int: bool is an int subclass
        return "true" if value else "false"
    if isinstance(value, int):
        return encode_number(value)
    if isinstance(value, float):
        return encode_number(value)
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, dict):
        return _encode_object(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode_value(item) for item in value) + "]"
    raise TypeError(f"cannot canonicalize value of type {type(value).__name__!r}")


def _encode_object(obj: dict) -> str:
    keyed = []
    for key in obj:
        if not isinstance(key, str):
            raise TypeError("JCS object keys must be strings")
        keyed.append(key)
    # Sort by UTF-16 code-unit sequence, per RFC 8785 section 3.2.3.
    ordered = sorted(keyed, key=_utf16_sort_key)
    parts = [f"{_encode_string(k)}:{_encode_value(obj[k])}" for k in ordered]
    return "{" + ",".join(parts) + "}"


def _encode_string(s: str) -> str:
    out = ['"']
    for ch in s:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _utf16_sort_key(s: str) -> tuple:
    """UTF-16 code-unit tuple used to order object member names.

    Python's default string comparison orders by Unicode code point, which
    disagrees with UTF-16 code-unit ordering for supplementary-plane
    characters (U+10000 and above): those encode as a surrogate pair whose
    leading unit (0xD800-0xDBFF) is numerically *below* the BMP private-use
    range (U+E000-U+FFFF), even though the code point itself is numerically
    higher. RFC 8785 mandates the UTF-16 ordering, so member names are
    re-encoded to UTF-16BE and compared as 16-bit unsigned integers.
    """
    encoded = s.encode("utf-16-be", "surrogatepass")
    return tuple(
        int.from_bytes(encoded[i : i + 2], "big") for i in range(0, len(encoded), 2)
    )


# --------------------------------------------------------------------------
# ECMAScript Number::toString (radix 10)
# --------------------------------------------------------------------------


def encode_number(value: Any) -> str:
    """Serialise ``value`` per the ECMAScript ``Number::toString`` algorithm.

    RFC 8785 section 3.2.2.3 requires every JSON number to be formatted as
    ECMA-262 would format it as a ``Number``. That algorithm always starts
    from the *shortest decimal digit string that round-trips* to the
    original IEEE-754 double, then lays those digits out as a plain
    integer, a fixed-point decimal, or exponential notation depending on
    the decimal exponent ``n``:

    - ``k <= n <= 21``:  digits, then ``n - k`` trailing zeros (plain integer)
    - ``0 < n <= 21``:   digits with the decimal point after position ``n``
    - ``-6 < n <= 0``:   ``"0."`` + ``-n`` zeros + digits
    - otherwise:         exponential, ``d1[.d2..dk]e±exp``

    where ``k`` is the digit count and the value equals ``digits * 10**(n - k)``.

    For a Python ``int`` the digit string is exact (arbitrary precision);
    for a ``float`` it is derived from ``repr()``, which Python guarantees
    to be the shortest string that reparses to the same double — the same
    guarantee the ECMAScript algorithm relies on.
    """
    if isinstance(value, bool):
        raise TypeError("bool is not a JSON number")
    if isinstance(value, int):
        return _int_to_es_string(value)
    if isinstance(value, float):
        return _float_to_es_string(value)
    raise TypeError(f"not a JSON number: {value!r}")


def _int_to_es_string(value: int) -> str:
    if value == 0:
        return "0"
    negative = value < 0
    digits = str(-value if negative else value)
    body = _format_digits(*_strip_trailing_zeros(digits, exponent=0))
    return "-" + body if negative else body


def _float_to_es_string(value: float) -> str:
    if value != value:  # NaN
        raise ValueError("NaN is not a valid JSON number")
    if value in (float("inf"), float("-inf")):
        raise ValueError("Infinity is not a valid JSON number")
    if value == 0.0:
        return "0"  # covers -0.0 too: ES ToString(-0) === "0"
    negative = value < 0
    digits, exponent = _shortest_round_trip_digits(-value if negative else value)
    body = _format_digits(*_strip_trailing_zeros(digits, exponent))
    return "-" + body if negative else body


def _shortest_round_trip_digits(abs_value: float) -> tuple:
    """Return (digit_string, exponent) with value == int(digit_string) * 10**exponent.

    Built from ``repr(abs_value)``, which is Python's shortest round-tripping
    decimal representation of the double (the same property ECMAScript's
    algorithm requires).
    """
    text = repr(abs_value)
    if "e" in text or "E" in text:
        mantissa, exp_text = _EXP_RE.split(text)
        exp = int(exp_text)
    else:
        mantissa, exp = text, 0
    if "." in mantissa:
        int_part, frac_part = mantissa.split(".")
    else:
        int_part, frac_part = mantissa, ""
    combined = (int_part + frac_part).lstrip("0")
    exponent = exp - len(frac_part)
    if not combined:
        return "0", 0
    return combined, exponent


def _strip_trailing_zeros(digits: str, exponent: int) -> tuple:
    stripped = digits.rstrip("0")
    exponent += len(digits) - len(stripped)
    return (stripped or "0"), exponent


def _format_digits(digits: str, exponent: int) -> str:
    """Lay out ``digits * 10**exponent`` per ECMAScript Number::toString steps 5-9."""
    k = len(digits)
    n = exponent + k
    if k <= n <= 21:
        return digits + "0" * (n - k)
    if 0 < n <= 21:
        return digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return "0." + "0" * (-n) + digits
    exp = n - 1
    sign = "+" if exp >= 0 else "-"
    mantissa = digits if k == 1 else f"{digits[0]}.{digits[1:]}"
    return f"{mantissa}e{sign}{abs(exp)}"
