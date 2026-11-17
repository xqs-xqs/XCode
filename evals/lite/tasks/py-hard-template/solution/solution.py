"""A small placeholder template renderer."""

import re

_SEGMENT = re.compile(r"[A-Za-z0-9_]+")
_FILTERS = {
    "upper": str.upper,
    "lower": str.lower,
    "title": str.title,
    "trim": str.strip,
}


def _expand(inner: str, values) -> str:
    name, *filters = [piece.strip() for piece in inner.split("|")]
    segments = name.split(".")
    if any(_SEGMENT.fullmatch(segment) is None for segment in segments):
        raise ValueError(f"malformed placeholder {inner!r}")
    for filter_name in filters:
        if filter_name not in _FILTERS:
            raise ValueError(f"unknown filter {filter_name!r}")
    current = values
    for segment in segments:
        if not isinstance(current, dict):
            raise KeyError(segment)
        current = current[segment]
    text = str(current)
    for filter_name in filters:
        text = _FILTERS[filter_name](text)
    return text


def render(template: str, values: dict) -> str:
    output, index = [], 0
    while index < len(template):
        character = template[index]
        if character == "{":
            if template.startswith("{{", index):
                output.append("{")
                index += 2
                continue
            end = template.find("}", index + 1)
            if end == -1:
                raise ValueError("unclosed placeholder")
            inner = template[index + 1:end]
            if "{" in inner:
                raise ValueError("unclosed placeholder")
            output.append(_expand(inner, values))
            index = end + 1
        elif character == "}":
            if not template.startswith("}}", index):
                raise ValueError("unmatched }")
            output.append("}")
            index += 2
        else:
            output.append(character)
            index += 1
    return "".join(output)
