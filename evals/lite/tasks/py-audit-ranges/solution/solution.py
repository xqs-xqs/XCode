"""Compress integers into range notation and expand it again."""

import re

_ITEM = re.compile(r"\s*(-?[0-9]+)\s*(?:-\s*(-?[0-9]+))?\s*")


def compress(numbers) -> str:
    values = sorted(set(numbers))
    items = []
    index = 0
    while index < len(values):
        end = index
        while end + 1 < len(values) and values[end + 1] == values[end] + 1:
            end += 1
        if end - index >= 2:
            items.append(f"{values[index]}-{values[end]}")
        else:
            items.extend(str(value) for value in values[index:end + 1])
        index = end + 1
    return ",".join(items)


def expand(text: str) -> list:
    if not text.strip():
        return []
    values = set()
    for item in text.split(","):
        match = _ITEM.fullmatch(item)
        if match is None:
            raise ValueError(f"malformed item {item!r}")
        first = int(match.group(1))
        last = first if match.group(2) is None else int(match.group(2))
        if last < first:
            raise ValueError(f"descending range {item!r}")
        values.update(range(first, last + 1))
    return sorted(values)
