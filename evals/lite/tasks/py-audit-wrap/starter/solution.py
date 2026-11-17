"""Greedy word wrapping with paragraph support."""


def wrap(text: str, width: int) -> list:
    if width < 1:
        raise ValueError("width must be at least 1")
    paragraphs, current = [], []
    for line in text.split("\n"):
        if line.strip():
            current.extend(line.split())
        elif current:
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)

    lines = []
    for number, words in enumerate(paragraphs):
        line = ""
        for word in words:
            if len(word) > width:
                if line:
                    lines.append(line)
                chunks = [word[start:start + width] for start in range(0, len(word), width)]
                lines.extend(chunks)
                line = ""
            elif not line:
                line = word
            elif len(line) + 1 + len(word) < width:
                line += " " + word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines
