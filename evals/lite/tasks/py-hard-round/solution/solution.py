"""Exact half-even rounding of decimal strings."""

import re
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

_NUMBER = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")


def round_decimal(text: str, places: int) -> str:
    if places < 0:
        raise ValueError("places must not be negative")
    if not isinstance(text, str) or _NUMBER.fullmatch(text) is None:
        raise ValueError(f"malformed number {text!r}")
    with localcontext() as context:
        context.prec = len(text) + places + 5
        value = Decimal(text).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    rendered = format(value, "f")
    return rendered.lstrip("-") if value == 0 else rendered
