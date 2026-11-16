"""Render rows as an aligned plain-text table."""


def _text(cell) -> str:
    if cell is None:
        return ""
    if isinstance(cell, bool):
        return "yes" if cell else "no"
    if isinstance(cell, float):
        return f"{cell:.2f}"
    return str(cell)


def _numeric(cell) -> bool:
    return isinstance(cell, (int, float)) and not isinstance(cell, bool)


def format_table(headers: list, rows: list) -> str:
    if not headers:
        raise ValueError("headers must not be empty")
    padded = []
    for row in rows:
        if len(row) > len(headers):
            raise ValueError("row has more cells than headers")
        padded.append(list(row) + [None] * (len(headers) - len(row)))
    widths = [len(header) for header in headers]
    for row in padded:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(_text(cell)))
    lines = [
        "  ".join(header.ljust(width) for header, width in zip(headers, widths)),
        "  ".join("-" * width for width in widths),
    ]
    for row in padded:
        cells = []
        for cell, width in zip(row, widths):
            cells.append(_text(cell).rjust(width) if _numeric(cell) else _text(cell).ljust(width))
        lines.append("  ".join(cells))
    return "\n".join(line.rstrip() for line in lines)
