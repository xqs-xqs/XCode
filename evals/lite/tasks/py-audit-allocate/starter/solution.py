"""Largest-remainder allocation of an integer amount."""


def allocate(total: int, weights: list) -> list:
    if not isinstance(total, int):
        raise TypeError("total must be an int")
    weights = list(weights)
    for weight in weights:
        if isinstance(weight, bool) or not isinstance(weight, int):
            raise TypeError("weights must be ints")
    if not weights:
        raise ValueError("weights must not be empty")
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must not be negative")
    scale = sum(weights)
    if scale == 0:
        return [0] * len(weights)
    amount = abs(total)
    parts = [amount * weight // scale for weight in weights]
    remainders = [amount * weight % scale for weight in weights]
    order = sorted(range(len(weights)), key=lambda index: (-remainders[index], -index))
    for index in order[: amount - sum(parts)]:
        parts[index] += 1
    return parts
