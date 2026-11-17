"""Match versions against comparator specs."""

import re

_NUMBER = r"[0-9]+"
_FULL = re.compile(rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}")
_PARTIAL = re.compile(rf"{_NUMBER}(?:\.{_NUMBER}){{0,2}}")
_COMPARATOR = re.compile(r"(>=|<=|>|<|=|\^|~)?(.+)")


def _full(text):
    if not isinstance(text, str) or _FULL.fullmatch(text) is None:
        raise ValueError(f"malformed version {text!r}")
    return tuple(int(part) for part in text.split("."))


def _partial(text):
    if _PARTIAL.fullmatch(text) is None:
        raise ValueError(f"malformed version {text!r}")
    parts = [int(part) for part in text.split(".")]
    return tuple(parts + [0] * (3 - len(parts)))


def _comparator(token):
    if token == "*":
        return lambda version: True
    match = _COMPARATOR.fullmatch(token)
    if match is None:
        raise ValueError(f"malformed comparator {token!r}")
    operator, base = match.group(1) or "=", _partial(match.group(2))
    if operator == "=":
        return lambda version: version == base
    if operator == ">":
        return lambda version: version > base
    if operator == ">=":
        return lambda version: version >= base
    if operator == "<":
        return lambda version: version < base
    if operator == "<=":
        return lambda version: version < base
    if operator == "^":
        major, minor, patch = base
        upper = (major + 1, 0, 0)
    else:
        upper = (base[0] + 1, 0, 0)
    return lambda version: base <= version < upper


def satisfies(version: str, spec: str) -> bool:
    parsed = _full(version)
    if not isinstance(spec, str):
        raise ValueError("spec must be a string")
    alternatives = []
    for alternative in spec.split("||"):
        tokens = alternative.split()
        if not tokens:
            raise ValueError("empty alternative")
        alternatives.append([_comparator(token) for token in tokens])
    return any(all(check(parsed) for check in checks) for checks in alternatives)
