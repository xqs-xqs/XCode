"""Strict Roman numeral conversion."""

_SYMBOLS = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def to_roman(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("number must be an int")
    if not 1 <= number <= 3999:
        raise ValueError("number out of range")
    parts = []
    for value, symbol in _SYMBOLS:
        while number >= value:
            parts.append(symbol)
            number -= value
    return "".join(parts)


def from_roman(text: str) -> int:
    if not isinstance(text, str) or not text:
        raise ValueError("not a Roman numeral")
    total, position = 0, 0
    for value, symbol in _SYMBOLS:
        while text.startswith(symbol, position):
            total += value
            position += len(symbol)
    if position != len(text) or not 1 <= total <= 3999 or to_roman(total) != text:
        raise ValueError(f"not a standard Roman numeral: {text!r}")
    return total
