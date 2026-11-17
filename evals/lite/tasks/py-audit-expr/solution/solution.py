"""A recursive-descent evaluator for integer arithmetic."""

import re

_TOKEN = re.compile(r"\s*(?:([0-9]+)|(\*\*|//|[-+*%()]))")


def _tokens(text):
    tokens, position = [], 0
    stripped = text.rstrip()
    while position < len(stripped):
        match = _TOKEN.match(stripped, position)
        if match is None:
            raise ValueError(f"unexpected input at {position}")
        tokens.append(match.group(1) if match.group(1) is not None else match.group(2))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self):
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of expression")
        self.index += 1
        return token

    def expression(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            if self.take() == "+":
                value += self.term()
            else:
                value -= self.term()
        return value

    def term(self):
        value = self.unary()
        while self.peek() in ("*", "//", "%"):
            operator = self.take()
            right = self.unary()
            if operator == "*":
                value *= right
            elif operator == "//":
                value //= right
            else:
                value %= right
        return value

    def unary(self):
        if self.peek() == "-":
            self.take()
            return -self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == "**":
            self.take()
            exponent = self.unary()
            if exponent < 0:
                raise ValueError("negative exponent")
            return base ** exponent
        return base

    def atom(self):
        token = self.take()
        if token == "(":
            value = self.expression()
            if self.take() != ")":
                raise ValueError("expected )")
            return value
        if token.isdigit():
            return int(token)
        raise ValueError(f"unexpected token {token!r}")


def evaluate(text: str) -> int:
    parser = _Parser(_tokens(text))
    value = parser.expression()
    if parser.peek() is not None:
        raise ValueError(f"unexpected token {parser.peek()!r}")
    return value
