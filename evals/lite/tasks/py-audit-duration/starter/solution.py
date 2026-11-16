"""Parse and format durations such as 1h30m."""

import re

_UNITS = [("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
_PART = re.compile(r"([0-9]+)([a-zA-Z])")


def parse_duration(text: str) -> int:
    if not isinstance(text, str) or not text:
        raise ValueError("empty duration")
    position, total, next_unit = 0, 0, 0
    while position < len(text):
        match = _PART.match(text, position)
        if match is None:
            raise ValueError(f"malformed duration {text!r}")
        index = next((i for i, (unit, _) in enumerate(_UNITS) if unit == match.group(2).lower()), None)
        if index is None:
            raise ValueError(f"malformed duration {text!r}")
        total += int(match.group(1)) * _UNITS[index][1]
        next_unit = index + 1
        position = match.end()
    return total


def format_duration(seconds: int) -> str:
    if not isinstance(seconds, int):
        raise TypeError("seconds must be an int")
    if seconds < 0:
        raise ValueError("seconds must not be negative")
    parts = []
    for unit, size in _UNITS:
        count, seconds = divmod(seconds, size)
        if count:
            parts.append(f"{count}{unit}")
    return "".join(parts)
