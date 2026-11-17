"""Spec-heavy Python tasks: several interacting rules, visible tests on the basic path only.

The first lite families are solved by a single agent almost every time, which
leaves no room to compare collaboration topologies. This family is harder on
one axis only: each prompt states a handful of precise rules, the visible suite
exercises the ordinary path, and the hidden suite checks every stated rule.
An implementation can therefore pass everything the agent is able to run and
still be wrong. Every hidden assertion follows from the prompt text; nothing is
graded that the prompt does not state.

The family was written and calibrated before any model saw it.
"""

from __future__ import annotations

from families_python import py_task, stub_of

HARD = "hard"


def hard_task(id, prompt, solution, visible, hidden, acceptance):
    return py_task(id, HARD, prompt, stub_of(solution), solution, visible, hidden, acceptance, tags=("spec-heavy",))


def suite(imports: str, name: str, body: str) -> str:
    return f"import unittest\n\n{imports}\n\n\nclass {name}(unittest.TestCase):\n{body}\n\nif __name__ == \"__main__\":\n    unittest.main()\n"


# --------------------------------------------------------------------------- #
# duration
# --------------------------------------------------------------------------- #

DURATION_PROMPT = (
    "Implement `parse_duration(text)` and `format_duration(seconds)` in solution.py. A duration is one or more "
    "parts written without spaces, each a non-negative decimal integer followed by a unit: w (7 days), d, h, m, s. "
    "Units are lower case, must appear in that order from largest to smallest, and each unit may appear at most "
    "once. A part may exceed its natural range (\"90m\" is valid) and may have leading zeros. `parse_duration` "
    "returns the total number of seconds and raises ValueError for anything else, including the empty string, a "
    "unit without a number, a number without a unit, an unknown unit, repeated or out-of-order units, signs, "
    "spaces and decimals. `format_duration` takes a non-negative int number of seconds and returns the canonical "
    "form: largest units first, zero parts omitted, every part within its natural range (d < 7, h < 24, m < 60, "
    "s < 60), and \"0s\" for zero. It raises ValueError for a negative value and TypeError for anything that is "
    "not an int (bool is rejected too)."
)

DURATION_SOLUTION = '''"""Parse and format durations such as 1h30m."""

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
        index = next((i for i, (unit, _) in enumerate(_UNITS) if unit == match.group(2)), None)
        if index is None or index < next_unit:
            raise ValueError(f"malformed duration {text!r}")
        total += int(match.group(1)) * _UNITS[index][1]
        next_unit = index + 1
        position = match.end()
    return total


def format_duration(seconds: int) -> str:
    if isinstance(seconds, bool) or not isinstance(seconds, int):
        raise TypeError("seconds must be an int")
    if seconds < 0:
        raise ValueError("seconds must not be negative")
    if seconds == 0:
        return "0s"
    parts = []
    for unit, size in _UNITS:
        count, seconds = divmod(seconds, size)
        if count:
            parts.append(f"{count}{unit}")
    return "".join(parts)
'''

DURATION_VISIBLE = suite("from solution import format_duration, parse_duration", "TestDuration", '''    def test_parse(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("45s"), 45)

    def test_format(self):
        self.assertEqual(format_duration(5400), "1h30m")
        self.assertEqual(format_duration(45), "45s")
''')

DURATION_HIDDEN = suite("from solution import format_duration, parse_duration", "TestDurationRules", '''    def test_parse_all_units(self):
        self.assertEqual(parse_duration("1w2d3h4m5s"), 604800 + 2 * 86400 + 3 * 3600 + 4 * 60 + 5)
        self.assertEqual(parse_duration("1w"), 604800)

    def test_parse_out_of_range_part_and_leading_zeros(self):
        self.assertEqual(parse_duration("90m"), 5400)
        self.assertEqual(parse_duration("007s"), 7)
        self.assertEqual(parse_duration("0s"), 0)

    def test_parse_rejects_missing_pieces(self):
        for text in ("", "h", "30", "1h30"):
            with self.assertRaises(ValueError, msg=text):
                parse_duration(text)

    def test_parse_rejects_order_and_repeats(self):
        for text in ("30m1h", "1h1h", "1s1w", "1d2d"):
            with self.assertRaises(ValueError, msg=text):
                parse_duration(text)

    def test_parse_rejects_other_syntax(self):
        for text in ("1x", "1 h", "1h 30m", "-1h", "+1h", "1.5h", "1H", " 1h", "1h "):
            with self.assertRaises(ValueError, msg=text):
                parse_duration(text)

    def test_format_boundaries(self):
        self.assertEqual(format_duration(0), "0s")
        self.assertEqual(format_duration(59), "59s")
        self.assertEqual(format_duration(60), "1m")
        self.assertEqual(format_duration(3600), "1h")
        self.assertEqual(format_duration(86400), "1d")
        self.assertEqual(format_duration(604800), "1w")

    def test_format_mixed(self):
        self.assertEqual(format_duration(3661), "1h1m1s")
        self.assertEqual(format_duration(90061), "1d1h1m1s")
        self.assertEqual(format_duration(8 * 86400 + 5), "1w1d5s")

    def test_round_trip(self):
        for seconds in (1, 61, 3599, 86399, 604799, 1234567):
            self.assertEqual(parse_duration(format_duration(seconds)), seconds)

    def test_format_rejects_bad_values(self):
        with self.assertRaises(ValueError):
            format_duration(-1)
        for value in (1.5, "60", True, None):
            with self.assertRaises(TypeError, msg=repr(value)):
                format_duration(value)
''')

# --------------------------------------------------------------------------- #
# allocate
# --------------------------------------------------------------------------- #

ALLOCATE_PROMPT = (
    "Implement `allocate(total, weights)` in solution.py: split the integer `total` (an amount in cents) across "
    "the weights so that the parts are integers summing exactly to `total`. Each part starts as the floor of its "
    "exact proportional share of the absolute value of `total`; the cents left over are handed out one each to "
    "the parts with the largest fractional remainders, ties going to the earlier position. For a negative total, "
    "allocate the absolute value and negate every part. Weights are non-negative ints and a zero weight always "
    "receives 0. The result is a list in the order of the weights and must be exact for arbitrarily large "
    "integers. Raise ValueError if `weights` is empty, any weight is negative, or all weights are zero; raise "
    "TypeError if `total` or any weight is not an int (bool is rejected too)."
)

ALLOCATE_SOLUTION = '''"""Largest-remainder allocation of an integer amount."""


def allocate(total: int, weights: list) -> list:
    if isinstance(total, bool) or not isinstance(total, int):
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
        raise ValueError("at least one weight must be positive")
    amount = abs(total)
    parts = [amount * weight // scale for weight in weights]
    remainders = [amount * weight % scale for weight in weights]
    order = sorted(range(len(weights)), key=lambda index: (-remainders[index], index))
    for index in order[: amount - sum(parts)]:
        parts[index] += 1
    return [-part for part in parts] if total < 0 else parts
'''

ALLOCATE_VISIBLE = suite("from solution import allocate", "TestAllocate", '''    def test_even_split(self):
        self.assertEqual(allocate(100, [1, 1]), [50, 50])

    def test_weighted_split(self):
        self.assertEqual(allocate(100, [1, 3]), [25, 75])
''')

ALLOCATE_HIDDEN = suite("from solution import allocate", "TestAllocateRules", '''    def test_leftover_goes_to_largest_remainder(self):
        self.assertEqual(allocate(100, [1, 2]), [33, 67])
        self.assertEqual(allocate(10, [1, 1, 4]), [2, 2, 6])

    def test_ties_go_to_earlier_position(self):
        self.assertEqual(allocate(100, [1, 1, 1]), [34, 33, 33])
        self.assertEqual(allocate(5, [1, 1]), [3, 2])
        self.assertEqual(allocate(1, [1, 1, 1, 1]), [1, 0, 0, 0])
        self.assertEqual(allocate(2, [1, 1, 1]), [1, 1, 0])

    def test_zero_weight_gets_nothing(self):
        self.assertEqual(allocate(10, [0, 1, 0]), [0, 10, 0])
        self.assertEqual(allocate(100, [1, 0, 1, 0, 1]), [34, 0, 33, 0, 33])

    def test_zero_total(self):
        self.assertEqual(allocate(0, [1, 2]), [0, 0])

    def test_negative_total(self):
        self.assertEqual(allocate(-100, [1, 1, 1]), [-34, -33, -33])
        self.assertEqual(allocate(-5, [1, 1]), [-3, -2])

    def test_exact_for_large_integers(self):
        self.assertEqual(allocate(10 ** 18 + 1, [1, 1]), [5 * 10 ** 17 + 1, 5 * 10 ** 17])
        self.assertEqual(allocate(10 ** 30, [1, 2]), [(10 ** 30) // 3, 10 ** 30 - (10 ** 30) // 3])

    def test_sum_is_preserved(self):
        for total in (1, 7, 99, 1001, -13):
            for weights in ([3, 5, 7], [1, 1, 1, 1, 1, 1, 1], [9, 1]):
                self.assertEqual(sum(allocate(total, weights)), total)

    def test_value_errors(self):
        for weights in ([], [0, 0], [1, -1]):
            with self.assertRaises(ValueError, msg=repr(weights)):
                allocate(10, weights)

    def test_type_errors(self):
        with self.assertRaises(TypeError):
            allocate(10.0, [1, 1])
        with self.assertRaises(TypeError):
            allocate(10, [1, 1.5])
        with self.assertRaises(TypeError):
            allocate(True, [1, 1])
        with self.assertRaises(TypeError):
            allocate(10, [1, True])
''')

# --------------------------------------------------------------------------- #
# number ranges
# --------------------------------------------------------------------------- #

RANGES_PROMPT = (
    "Implement `compress(numbers)` and `expand(text)` in solution.py. `compress` takes any iterable of ints, "
    "removes duplicates, sorts ascending and writes the numbers as comma-separated items with no spaces: a run of "
    "three or more consecutive integers becomes `first-last`, shorter runs are written as single numbers. "
    "Negative numbers keep their sign, so the run -3, -2, -1 is written `-3--1`. An empty input gives the empty "
    "string. `expand` is the inverse and returns a sorted list without duplicates. It accepts the same syntax "
    "and is more lenient: spaces are allowed around commas and around the range dash, a range may have any "
    "length of at least one (`4-4` is just 4 and `1-2` is fine), and items may come in any order and may "
    "overlap. An empty or whitespace-only string expands to []. `expand` raises ValueError for a descending "
    "range such as `5-3`, for an empty item (as in `1,,2` or a leading or trailing comma) and for any item that "
    "is not an integer or a range of two integers."
)

RANGES_SOLUTION = '''"""Compress integers into range notation and expand it again."""

import re

_ITEM = re.compile(r"\\s*(-?[0-9]+)\\s*(?:-\\s*(-?[0-9]+))?\\s*")


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
'''

RANGES_VISIBLE = suite("from solution import compress, expand", "TestRanges", '''    def test_compress(self):
        self.assertEqual(compress([1, 2, 3, 5]), "1-3,5")

    def test_expand(self):
        self.assertEqual(expand("1-3,5"), [1, 2, 3, 5])
''')

RANGES_HIDDEN = suite("from solution import compress, expand", "TestRangeRules", '''    def test_compress_short_runs_stay_single(self):
        self.assertEqual(compress([1, 2, 3, 5, 7, 8]), "1-3,5,7,8")
        self.assertEqual(compress([1, 2, 4, 5, 6]), "1,2,4-6")
        self.assertEqual(compress([5]), "5")

    def test_compress_sorts_and_dedupes(self):
        self.assertEqual(compress([3, 1, 2, 2]), "1-3")
        self.assertEqual(compress([10, 9, 8, 8]), "8-10")
        self.assertEqual(compress(value for value in (4, 3, 2)), "2-4")

    def test_compress_negatives(self):
        self.assertEqual(compress([-3, -2, -1]), "-3--1")
        self.assertEqual(compress([-3, -2, -1, 0, 1]), "-3-1")
        self.assertEqual(compress([-2, -1]), "-2,-1")
        self.assertEqual(compress([-5, -3]), "-5,-3")

    def test_compress_empty(self):
        self.assertEqual(compress([]), "")

    def test_expand_lenient_syntax(self):
        self.assertEqual(expand(" 1 - 3 , 5 "), [1, 2, 3, 5])
        self.assertEqual(expand("4-4"), [4])
        self.assertEqual(expand("1-2"), [1, 2])

    def test_expand_order_and_overlap(self):
        self.assertEqual(expand("5,1-2,2-3"), [1, 2, 3, 5])
        self.assertEqual(expand("3,3,3"), [3])

    def test_expand_negatives(self):
        self.assertEqual(expand("-3--1"), [-3, -2, -1])
        self.assertEqual(expand("-3-1"), [-3, -2, -1, 0, 1])
        self.assertEqual(expand("-2,-1"), [-2, -1])

    def test_expand_empty(self):
        self.assertEqual(expand(""), [])
        self.assertEqual(expand("   "), [])

    def test_expand_errors(self):
        for text in ("5-3", "1,,2", ",1", "1,", "a", "1-2-3", "1.5", "1-", "1 2"):
            with self.assertRaises(ValueError, msg=text):
                expand(text)

    def test_round_trip(self):
        for values in ([1, 2, 3, 5, 7, 8], [-4, -3, -2, 0, 9], [100]):
            self.assertEqual(expand(compress(values)), values)
''')

# --------------------------------------------------------------------------- #
# version ranges
# --------------------------------------------------------------------------- #

SEMVER_PROMPT = (
    "Implement `satisfies(version, spec)` in solution.py and return a bool. A version is `MAJOR.MINOR.PATCH`: "
    "three non-negative integers without leading zeros (a lone 0 is fine). A spec is one or more alternatives "
    "separated by `||`; the version satisfies the spec if it satisfies any alternative. An alternative is one or "
    "more comparators separated by whitespace, all of which must hold. Comparators: a bare version or `=version` "
    "(equal); `>`, `>=`, `<`, `<=` followed directly by a version; `^version` (at least that version and below "
    "the next version that increments its left-most non-zero component: ^1.2.3 is below 2.0.0, ^0.2.3 is below "
    "0.3.0, ^0.0.3 is below 0.0.4, and ^0.0.0 is below 0.0.1); `~version` (at least that version and below the "
    "next minor version: ~1.2.3 is below 1.3.0); and `*`, which any version satisfies. Inside a comparator the "
    "version may leave out trailing components, which count as zero before any rule is applied (`>=1.2` means "
    "`>=1.2.0`, `^1` means `^1.0.0`). The `version` argument itself must have all three components. Raise "
    "ValueError for a malformed version or spec: an empty spec or empty alternative, an unknown operator, "
    "whitespace between an operator and its version, leading zeros, more than three components, or non-digit "
    "components. A malformed spec raises even when another alternative already matches."
)

SEMVER_SOLUTION = '''"""Match versions against comparator specs."""

import re

_NUMBER = r"(?:0|[1-9][0-9]*)"
_FULL = re.compile(rf"{_NUMBER}\\.{_NUMBER}\\.{_NUMBER}")
_PARTIAL = re.compile(rf"{_NUMBER}(?:\\.{_NUMBER}){{0,2}}")
_COMPARATOR = re.compile(r"(>=|<=|>|<|=|\\^|~)?(.+)")


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
        return lambda version: version <= base
    if operator == "^":
        major, minor, patch = base
        if major > 0:
            upper = (major + 1, 0, 0)
        elif minor > 0:
            upper = (0, minor + 1, 0)
        else:
            upper = (0, 0, patch + 1)
    else:
        upper = (base[0], base[1] + 1, 0)
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
'''

SEMVER_VISIBLE = suite("from solution import satisfies", "TestSatisfies", '''    def test_exact(self):
        self.assertTrue(satisfies("1.2.3", "1.2.3"))
        self.assertFalse(satisfies("1.2.4", "1.2.3"))

    def test_range(self):
        self.assertTrue(satisfies("1.5.0", ">=1.2.0 <2.0.0"))
        self.assertFalse(satisfies("2.0.0", ">=1.2.0 <2.0.0"))

    def test_caret(self):
        self.assertTrue(satisfies("1.9.9", "^1.2.3"))
''')

SEMVER_HIDDEN = suite("from solution import satisfies", "TestSatisfiesRules", '''    def test_equal_forms(self):
        self.assertTrue(satisfies("1.2.3", "=1.2.3"))
        self.assertFalse(satisfies("1.2.3", "=1.2.4"))

    def test_comparators_compare_numerically(self):
        self.assertTrue(satisfies("1.10.0", ">1.9.0"))
        self.assertFalse(satisfies("1.9.0", ">1.10.0"))
        self.assertTrue(satisfies("1.2.3", "<=1.2.3"))
        self.assertFalse(satisfies("1.2.3", "<1.2.3"))
        self.assertFalse(satisfies("1.2.3", ">1.2.3"))

    def test_caret_major(self):
        self.assertTrue(satisfies("1.2.3", "^1.2.3"))
        self.assertFalse(satisfies("1.2.2", "^1.2.3"))
        self.assertFalse(satisfies("2.0.0", "^1.2.3"))

    def test_caret_zero_major(self):
        self.assertTrue(satisfies("0.2.9", "^0.2.3"))
        self.assertFalse(satisfies("0.3.0", "^0.2.3"))
        self.assertTrue(satisfies("0.0.3", "^0.0.3"))
        self.assertFalse(satisfies("0.0.4", "^0.0.3"))
        self.assertTrue(satisfies("0.0.0", "^0.0.0"))
        self.assertFalse(satisfies("0.0.1", "^0.0.0"))

    def test_tilde(self):
        self.assertTrue(satisfies("1.2.9", "~1.2.3"))
        self.assertFalse(satisfies("1.3.0", "~1.2.3"))
        self.assertFalse(satisfies("1.2.2", "~1.2.3"))

    def test_partial_versions_are_padded(self):
        self.assertTrue(satisfies("1.2.0", ">=1.2"))
        self.assertTrue(satisfies("1.0.0", "1"))
        self.assertFalse(satisfies("1.0.1", "1"))
        self.assertTrue(satisfies("1.9.0", "^1"))
        self.assertFalse(satisfies("2.0.0", "^1"))
        self.assertTrue(satisfies("1.0.5", "~1"))
        self.assertFalse(satisfies("1.1.0", "~1"))
        self.assertFalse(satisfies("0.0.1", "^0"))

    def test_star(self):
        self.assertTrue(satisfies("0.0.0", "*"))
        self.assertTrue(satisfies("9.9.9", "* >=1.0.0"))
        self.assertFalse(satisfies("0.9.9", "* >=1.0.0"))

    def test_alternatives(self):
        self.assertTrue(satisfies("3.1.0", "^1.0.0 || ^3.0.0"))
        self.assertFalse(satisfies("2.1.0", "^1.0.0 || ^3.0.0"))
        self.assertTrue(satisfies("1.0.0", "1.0.0||2.0.0"))

    def test_malformed_version(self):
        for version in ("1.2", "1.2.3.4", "01.2.3", "1.2.x", "", "v1.2.3", "1.2.3 "):
            with self.assertRaises(ValueError, msg=version):
                satisfies(version, "*")

    def test_malformed_spec(self):
        for spec in ("", "   ", "1.2.3 ||", "|| 1.2.3", ">= 1.2.3", "=>1.2.3", "!1.2.3", "^01.0.0", "1.2.3.4", "^", "~x"):
            with self.assertRaises(ValueError, msg=spec):
                satisfies("1.2.3", spec)

    def test_malformed_spec_raises_even_after_a_match(self):
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "1.2.3 || bogus")
''')

# --------------------------------------------------------------------------- #
# expression evaluator
# --------------------------------------------------------------------------- #

EXPR_PROMPT = (
    "Implement `evaluate(text)` in solution.py: evaluate an integer arithmetic expression and return an int. "
    "Tokens are non-negative decimal integer literals, the binary operators + - * // % **, unary minus, "
    "parentheses, and optional spaces between tokens; a space is not allowed inside a number or inside the "
    "two-character operators // and **. Precedence from lowest to highest: + and -; then *, // and %; then unary "
    "minus; then **. Binary operators of the same level are left-associative except **, which is "
    "right-associative. ** binds tighter than a unary minus on its left, so -2**2 is -4, while its exponent may "
    "itself start with a unary minus. // and % follow Python's floor semantics for negative operands. Raise "
    "ZeroDivisionError for // or % by zero, ValueError for a negative exponent, and ValueError for every syntax "
    "error: empty input, an unknown character, unbalanced parentheses, a missing operand, a single /, a unary "
    "plus, or two numbers in a row. Do not call eval or exec."
)

EXPR_SOLUTION = '''"""A recursive-descent evaluator for integer arithmetic."""

import re

_TOKEN = re.compile(r"\\s*(?:([0-9]+)|(\\*\\*|//|[-+*%()]))")


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
'''

EXPR_VISIBLE = suite("from solution import evaluate", "TestEvaluate", '''    def test_precedence(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)

    def test_parentheses(self):
        self.assertEqual(evaluate("(1 + 2) * 3"), 9)

    def test_floor_division(self):
        self.assertEqual(evaluate("7 // 2"), 3)
''')

EXPR_HIDDEN = suite("import inspect\nimport re\n\nimport solution\nfrom solution import evaluate", "TestEvaluateRules", '''    def test_power_and_unary_minus(self):
        self.assertEqual(evaluate("-2**2"), -4)
        self.assertEqual(evaluate("(-2)**2"), 4)
        self.assertEqual(evaluate("2**3**2"), 512)
        self.assertEqual(evaluate("2 ** -0"), 1)
        self.assertEqual(evaluate("0**0"), 1)

    def test_negative_exponent(self):
        with self.assertRaises(ValueError):
            evaluate("2**-1")
        with self.assertRaises(ValueError):
            evaluate("2**(1-3)")

    def test_unary_minus_positions(self):
        self.assertEqual(evaluate("--3"), 3)
        self.assertEqual(evaluate("2--3"), 5)
        self.assertEqual(evaluate("2*-3"), -6)
        self.assertEqual(evaluate("-(3)"), -3)
        self.assertEqual(evaluate("-(-3)"), 3)

    def test_floor_semantics(self):
        self.assertEqual(evaluate("-7//2"), -4)
        self.assertEqual(evaluate("7//-2"), -4)
        self.assertEqual(evaluate("-7%3"), 2)
        self.assertEqual(evaluate("7%-3"), -2)

    def test_left_associativity(self):
        self.assertEqual(evaluate("10-4-3"), 3)
        self.assertEqual(evaluate("100//3//2"), 16)
        self.assertEqual(evaluate("10%3*2"), 2)
        self.assertEqual(evaluate("2*3%4"), 2)

    def test_zero_division(self):
        for text in ("1//0", "1%0", "1//(2-2)"):
            with self.assertRaises(ZeroDivisionError, msg=text):
                evaluate(text)

    def test_spaces_and_big_numbers(self):
        self.assertEqual(evaluate("  12 + 3 "), 15)
        self.assertEqual(evaluate("2**100"), 2 ** 100)
        self.assertEqual(evaluate("( ( 4 ) )"), 4)

    def test_syntax_errors(self):
        for text in ("", "   ", "1 2", "1 +", "* 2", "(1+2", "1+2)", "()", "1/2", "+1", "1 + +2",
                     "2 * * 3", "4 / / 2", "a", "1.5", "2^3", "1 = 1"):
            with self.assertRaises(ValueError, msg=text):
                evaluate(text)

    def test_does_not_call_eval_or_exec(self):
        source = inspect.getsource(solution)
        self.assertIsNone(re.search(r"\\b(eval|exec)\\s*\\(", source))
''')

# --------------------------------------------------------------------------- #
# word wrap
# --------------------------------------------------------------------------- #

WRAP_PROMPT = (
    "Implement `wrap(text, width)` in solution.py and return a list of lines. Paragraphs are separated by one or "
    "more blank lines (a blank line is empty or holds only whitespace) and are wrapped independently; in the "
    "output, consecutive paragraphs are separated by exactly one empty string, and there is no empty string "
    "before the first or after the last paragraph. Inside a paragraph, words are maximal runs of non-whitespace "
    "characters; all whitespace, single newlines included, only separates words. Lines are filled greedily: a "
    "word joins the current line when the line, one space and the word together fit within `width`, otherwise it "
    "starts a new line. A word longer than `width` always starts on a new line and is cut into chunks of exactly "
    "`width` characters, the last chunk possibly shorter; the next word may join that last chunk if it fits. No "
    "line has leading or trailing spaces. Text without any word gives []. Raise ValueError when `width` is less "
    "than 1."
)

WRAP_SOLUTION = '''"""Greedy word wrapping with paragraph support."""


def wrap(text: str, width: int) -> list:
    if width < 1:
        raise ValueError("width must be at least 1")
    paragraphs, current = [], []
    for line in text.split("\\n"):
        if line.strip():
            current.extend(line.split())
        elif current:
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)

    lines = []
    for number, words in enumerate(paragraphs):
        if number:
            lines.append("")
        line = ""
        for word in words:
            if len(word) > width:
                if line:
                    lines.append(line)
                chunks = [word[start:start + width] for start in range(0, len(word), width)]
                lines.extend(chunks[:-1])
                line = chunks[-1]
            elif not line:
                line = word
            elif len(line) + 1 + len(word) <= width:
                line += " " + word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines
'''

WRAP_VISIBLE = suite("from solution import wrap", "TestWrap", '''    def test_simple(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_short_text(self):
        self.assertEqual(wrap("hi", 10), ["hi"])
''')

WRAP_HIDDEN = suite("from solution import wrap", "TestWrapRules", '''    def test_exact_fit(self):
        self.assertEqual(wrap("a b c", 3), ["a b", "c"])
        self.assertEqual(wrap("hello world", 11), ["hello world"])
        self.assertEqual(wrap("hello world", 10), ["hello", "world"])

    def test_whitespace_only_separates_words(self):
        self.assertEqual(wrap("  a \\t b\\nc  ", 10), ["a b c"])

    def test_long_word_is_cut(self):
        self.assertEqual(wrap("abcdefgh", 3), ["abc", "def", "gh"])
        self.assertEqual(wrap("abcdef", 3), ["abc", "def"])

    def test_long_word_starts_new_line(self):
        self.assertEqual(wrap("x abcdefgh y", 3), ["x", "abc", "def", "gh", "y"])

    def test_next_word_may_join_last_chunk(self):
        self.assertEqual(wrap("x abcdef y", 4), ["x", "abcd", "ef y"])
        self.assertEqual(wrap("abcdef yz", 4), ["abcd", "ef", "yz"])

    def test_paragraphs(self):
        self.assertEqual(wrap("a\\n\\nb", 5), ["a", "", "b"])
        self.assertEqual(wrap("a b\\n \\t \\n\\n\\nc d", 3), ["a b", "", "c d"])

    def test_no_empty_string_at_the_edges(self):
        self.assertEqual(wrap("\\n\\na\\n\\n", 5), ["a"])
        self.assertEqual(wrap("\\n \\n a b \\n\\n c \\n \\n", 5), ["a b", "", "c"])

    def test_no_words(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("  \\n \\t\\n", 5), [])

    def test_width_one(self):
        self.assertEqual(wrap("ab c", 1), ["a", "b", "c"])

    def test_no_edge_spaces(self):
        for line in wrap("one  two   three four five six seven", 9):
            self.assertEqual(line, line.strip())
            self.assertLessEqual(len(line), 9)

    def test_invalid_width(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("a", width)
''')

# --------------------------------------------------------------------------- #
# interval set
# --------------------------------------------------------------------------- #

INTERVALS_PROMPT = (
    "Implement the class `IntervalSet` in solution.py: a set of integers stored as half-open intervals "
    "[start, end). The constructor takes no arguments. `add(start, end)` inserts every integer of the interval; "
    "`remove(start, end)` deletes them; `contains(value)` tests membership; `intervals()` returns the content as "
    "a list of (start, end) tuples sorted by start, in which no two intervals overlap or touch (touching "
    "intervals such as [1, 3) and [3, 5) are merged into (1, 5)); `len(obj)` gives the number of integers "
    "stored. `add` and `remove` raise ValueError when start > end and do nothing when start == end. Removing "
    "from the middle of an interval splits it in two."
)

INTERVALS_SOLUTION = '''"""A set of integers kept as merged half-open intervals."""


class IntervalSet:
    def __init__(self):
        self._items = []

    def add(self, start, end):
        if start > end:
            raise ValueError("start must not exceed end")
        if start == end:
            return
        merged, placed = [], False
        for low, high in self._items:
            if high < start:
                merged.append((low, high))
            elif end < low:
                if not placed:
                    merged.append((start, end))
                    placed = True
                merged.append((low, high))
            else:
                start, end = min(start, low), max(end, high)
        if not placed:
            merged.append((start, end))
        self._items = merged

    def remove(self, start, end):
        if start > end:
            raise ValueError("start must not exceed end")
        if start == end:
            return
        kept = []
        for low, high in self._items:
            if high <= start or end <= low:
                kept.append((low, high))
                continue
            if low < start:
                kept.append((low, start))
            if end < high:
                kept.append((end, high))
        self._items = kept

    def contains(self, value):
        return any(low <= value < high for low, high in self._items)

    def intervals(self):
        return list(self._items)

    def __len__(self):
        return sum(high - low for low, high in self._items)
'''

INTERVALS_VISIBLE = suite("from solution import IntervalSet", "TestIntervalSet", '''    def test_add_and_contains(self):
        items = IntervalSet()
        items.add(1, 4)
        self.assertTrue(items.contains(1))
        self.assertTrue(items.contains(3))
        self.assertFalse(items.contains(4))

    def test_two_separate_intervals(self):
        items = IntervalSet()
        items.add(5, 7)
        items.add(1, 3)
        self.assertEqual(items.intervals(), [(1, 3), (5, 7)])
''')

INTERVALS_HIDDEN = suite("from solution import IntervalSet", "TestIntervalSetRules", '''    def build(self, *pairs):
        items = IntervalSet()
        for start, end in pairs:
            items.add(start, end)
        return items

    def test_touching_intervals_merge(self):
        self.assertEqual(self.build((1, 3), (3, 5)).intervals(), [(1, 5)])
        self.assertEqual(self.build((3, 5), (1, 3)).intervals(), [(1, 5)])

    def test_overlapping_and_contained(self):
        self.assertEqual(self.build((1, 5), (3, 8)).intervals(), [(1, 8)])
        self.assertEqual(self.build((1, 10), (3, 4)).intervals(), [(1, 10)])
        self.assertEqual(self.build((3, 4), (1, 10)).intervals(), [(1, 10)])

    def test_add_bridges_several(self):
        self.assertEqual(self.build((1, 2), (4, 5), (7, 8), (2, 7)).intervals(), [(1, 8)])
        self.assertEqual(self.build((1, 2), (4, 5), (7, 8), (3, 6)).intervals(), [(1, 2), (3, 6), (7, 8)])

    def test_gap_of_one_does_not_merge(self):
        self.assertEqual(self.build((1, 3), (4, 6)).intervals(), [(1, 3), (4, 6)])

    def test_remove_splits(self):
        items = self.build((1, 10))
        items.remove(4, 6)
        self.assertEqual(items.intervals(), [(1, 4), (6, 10)])
        self.assertFalse(items.contains(4))
        self.assertFalse(items.contains(5))
        self.assertTrue(items.contains(6))

    def test_remove_edges_and_whole(self):
        items = self.build((1, 10))
        items.remove(0, 3)
        items.remove(8, 20)
        self.assertEqual(items.intervals(), [(3, 8)])
        items.remove(3, 8)
        self.assertEqual(items.intervals(), [])

    def test_remove_across_several(self):
        items = self.build((1, 3), (5, 7), (9, 11))
        items.remove(2, 10)
        self.assertEqual(items.intervals(), [(1, 2), (10, 11)])

    def test_remove_nothing(self):
        items = self.build((1, 3))
        items.remove(3, 5)
        items.remove(-5, 1)
        self.assertEqual(items.intervals(), [(1, 3)])

    def test_len(self):
        items = self.build((1, 4), (10, 12))
        self.assertEqual(len(items), 5)
        items.remove(2, 3)
        self.assertEqual(len(items), 4)
        self.assertEqual(len(IntervalSet()), 0)

    def test_empty_interval_is_a_no_op(self):
        items = self.build((1, 3))
        items.add(7, 7)
        items.remove(2, 2)
        self.assertEqual(items.intervals(), [(1, 3)])

    def test_reversed_bounds_raise(self):
        items = IntervalSet()
        with self.assertRaises(ValueError):
            items.add(5, 3)
        with self.assertRaises(ValueError):
            items.remove(5, 3)

    def test_negative_numbers(self):
        items = self.build((-5, -1), (-1, 2))
        self.assertEqual(items.intervals(), [(-5, 2)])
        self.assertTrue(items.contains(-5))
        self.assertFalse(items.contains(2))
''')

# --------------------------------------------------------------------------- #
# table formatting
# --------------------------------------------------------------------------- #

TABLE_PROMPT = (
    "Implement `format_table(headers, rows)` in solution.py and return one string. `headers` is a list of "
    "strings and `rows` a list of lists. Cell text: None becomes the empty string; True and False become `yes` "
    "and `no`; an int is written in decimal; a float is written with exactly two decimals; a str is used as it "
    "is. A column is as wide as its longest cell text or header. Ints and floats are right-aligned in their "
    "column; everything else, headers and booleans included, is left-aligned. The output has the header line, "
    "then a line made of one run of dashes per column as wide as that column, then one line per row. Columns "
    "are joined by two spaces, trailing spaces are removed from every line, and lines are joined by a newline "
    "with no newline at the end. A row with fewer cells than headers is padded with None; a row with more cells "
    "raises ValueError, and so does an empty `headers` list."
)

TABLE_SOLUTION = '''"""Render rows as an aligned plain-text table."""


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
    return "\\n".join(line.rstrip() for line in lines)
'''

TABLE_VISIBLE = suite("from solution import format_table", "TestFormatTable", '''    def test_strings(self):
        text = format_table(["name", "city"], [["Ann", "Oslo"], ["Robert", "Rome"]])
        self.assertEqual(text, "name    city\\n------  ----\\nAnn     Oslo\\nRobert  Rome")

    def test_numbers_align_right(self):
        text = format_table(["item", "qty"], [["nut", 5], ["bolt", 120]])
        self.assertEqual(text, "item  qty\\n----  ---\\nnut     5\\nbolt  120")
''')

TABLE_HIDDEN = suite("from solution import format_table", "TestFormatTableRules", '''    def test_floats_have_two_decimals(self):
        text = format_table(["v"], [[1.0], [2.25], [10.5]])
        self.assertEqual(text, "v\\n-----\\n 1.00\\n 2.25\\n10.50")

    def test_none_and_bool(self):
        text = format_table(["a", "ok"], [[None, True], ["x", False]])
        self.assertEqual(text, "a  ok\\n-  ---\\n   yes\\nx  no")

    def test_bool_is_left_aligned(self):
        text = format_table(["enabled"], [[True], [False]])
        self.assertEqual(text, "enabled\\n-------\\nyes\\nno")

    def test_header_wider_than_cells(self):
        text = format_table(["quantity"], [[1], [22]])
        self.assertEqual(text, "quantity\\n--------\\n       1\\n      22")

    def test_trailing_spaces_removed(self):
        text = format_table(["a", "b"], [["long text", None], ["x", "y"]])
        self.assertEqual(text, "a          b\\n---------  -\\nlong text\\nx          y")
        for line in text.split("\\n"):
            self.assertEqual(line, line.rstrip())

    def test_short_row_is_padded(self):
        text = format_table(["a", "b", "c"], [["x"], ["y", 2, 3]])
        self.assertEqual(text, "a  b  c\\n-  -  -\\nx\\ny  2  3")

    def test_mixed_column(self):
        text = format_table(["value"], [["abc"], [7], [None], ["z"]])
        self.assertEqual(text, "value\\n-----\\nabc\\n    7\\n\\nz")

    def test_negative_numbers(self):
        text = format_table(["n"], [[-5], [12], [-1.5]])
        self.assertEqual(text, "n\\n-----\\n   -5\\n   12\\n-1.50")

    def test_no_rows(self):
        self.assertEqual(format_table(["a", "bb"], []), "a  bb\\n-  --")

    def test_no_trailing_newline(self):
        self.assertFalse(format_table(["a"], [["x"]]).endswith("\\n"))

    def test_errors(self):
        with self.assertRaises(ValueError):
            format_table([], [])
        with self.assertRaises(ValueError):
            format_table(["a"], [["x", "y"]])
''')

# --------------------------------------------------------------------------- #
# template rendering
# --------------------------------------------------------------------------- #

TEMPLATE_PROMPT = (
    "Implement `render(template, values)` in solution.py and return a string. A placeholder `{name}` is replaced "
    "by str() of `values[name]`. A dotted name such as `{user.name}` walks nested dicts. `{{` and `}}` produce a "
    "literal `{` and `}`. Filters follow the name after a `|` and are applied left to right to the string value: "
    "`upper`, `lower`, `title` (str.title) and `trim` (strip surrounding whitespace), as in `{name|trim|upper}`. "
    "Whitespace around the name and around filter names is ignored (`{ name | upper }`). Each segment of a name "
    "consists of letters, digits and underscores and must not be empty. Raise KeyError when a name segment is "
    "missing or when a value that must be walked into is not a dict. Raise ValueError for an unknown filter, an "
    "empty filter, an empty placeholder, a malformed name, a `{` without a closing `}`, and a lone `}` outside a "
    "placeholder. Text outside placeholders is copied unchanged."
)

TEMPLATE_SOLUTION = '''"""A small placeholder template renderer."""

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
'''

TEMPLATE_VISIBLE = suite("from solution import render", "TestRender", '''    def test_placeholder(self):
        self.assertEqual(render("Hello {name}!", {"name": "Ada"}), "Hello Ada!")

    def test_filter(self):
        self.assertEqual(render("{name|upper}", {"name": "Ada"}), "ADA")

    def test_plain_text(self):
        self.assertEqual(render("no placeholders", {}), "no placeholders")
''')

TEMPLATE_HIDDEN = suite("from solution import render", "TestRenderRules", '''    def test_non_string_values(self):
        self.assertEqual(render("{n} items, {flag}, {x}", {"n": 3, "flag": True, "x": None}), "3 items, True, None")

    def test_dotted_names(self):
        values = {"user": {"name": "Ada", "address": {"city": "Paris"}}}
        self.assertEqual(render("{user.name} in {user.address.city}", values), "Ada in Paris")

    def test_escaped_braces(self):
        self.assertEqual(render("{{}}", {}), "{}")
        self.assertEqual(render("{{name}}", {"name": "x"}), "{name}")
        self.assertEqual(render("{{{name}}}", {"name": "x"}), "{x}")
        self.assertEqual(render("a }} b {{ c", {}), "a } b { c")

    def test_filters_chain_left_to_right(self):
        self.assertEqual(render("{v|trim|upper}", {"v": "  ab "}), "AB")
        self.assertEqual(render("{v|upper|lower}", {"v": "Ab"}), "ab")
        self.assertEqual(render("{v|title}", {"v": "hello world"}), "Hello World")
        self.assertEqual(render("[{v|trim}]", {"v": " x "}), "[x]")

    def test_whitespace_inside_placeholder(self):
        self.assertEqual(render("{ name | upper }", {"name": "ada"}), "ADA")
        self.assertEqual(render("{ user.name }", {"user": {"name": "ada"}}), "ada")

    def test_filter_applies_to_string_form(self):
        self.assertEqual(render("{n|upper}", {"n": 12}), "12")
        self.assertEqual(render("{flag|lower}", {"flag": True}), "true")

    def test_missing_names(self):
        with self.assertRaises(KeyError):
            render("{missing}", {})
        with self.assertRaises(KeyError):
            render("{user.age}", {"user": {"name": "x"}})
        with self.assertRaises(KeyError):
            render("{user.name.first}", {"user": {"name": "x"}})

    def test_unknown_or_empty_filter(self):
        for template in ("{name|shout}", "{name|}", "{name||upper}", "{name|upper|}"):
            with self.assertRaises(ValueError, msg=template):
                render(template, {"name": "x"})

    def test_malformed_placeholders(self):
        for template in ("{}", "{ }", "{a-b}", "{a..b}", "{.a}", "{a.}", "{|upper}", "{a b}"):
            with self.assertRaises(ValueError, msg=template):
                render(template, {"a": {"b": "x"}, "a-b": "x", "a b": "x"})

    def test_unbalanced_braces(self):
        for template in ("{name", "name}", "{name}}", "a { b", "}"):
            with self.assertRaises(ValueError, msg=template):
                render(template, {"name": "x"})

    def test_text_is_copied_unchanged(self):
        self.assertEqual(render("  a|b . c\\n", {}), "  a|b . c\\n")
''')

# --------------------------------------------------------------------------- #
# install order
# --------------------------------------------------------------------------- #

ORDER_PROMPT = (
    "Implement `install_order(packages)` in solution.py. `packages` maps each package name to the list of names "
    "it depends on. Return a list containing every package exactly once such that each package appears after "
    "all of its dependencies. Whenever several packages are ready at the same time, the alphabetically smallest "
    "goes first, so the result is unique. Duplicate entries in a dependency list are harmless. A dependency that "
    "is not a key of `packages` raises KeyError. A dependency cycle raises ValueError whose message is exactly "
    "the cycle written as names joined by ` -> `, starting and ending with the alphabetically smallest name in "
    "the cycle and following the dependency direction (`a -> b` means a depends on b); a package that depends on "
    "itself gives `a -> a`. The input dict must not be modified."
)

ORDER_SOLUTION = '''"""Deterministic dependency ordering with cycle reporting."""

import heapq


def install_order(packages: dict) -> list:
    dependencies = {}
    for name, needs in packages.items():
        for need in needs:
            if need not in packages:
                raise KeyError(need)
        dependencies[name] = set(needs)

    dependents = {name: [] for name in dependencies}
    for name, needs in dependencies.items():
        for need in needs:
            dependents[need].append(name)
    waiting = {name: len(needs) for name, needs in dependencies.items()}
    ready = [name for name, count in waiting.items() if count == 0]
    heapq.heapify(ready)

    order = []
    while ready:
        name = heapq.heappop(ready)
        order.append(name)
        for dependent in dependents[name]:
            waiting[dependent] -= 1
            if waiting[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) == len(dependencies):
        return order

    done = set(order)
    path, seen = [], {}
    current = min(name for name in dependencies if name not in done)
    while current not in seen:
        seen[current] = len(path)
        path.append(current)
        current = min(need for need in dependencies[current] if need not in done)
    cycle = path[seen[current]:]
    start = cycle.index(min(cycle))
    cycle = cycle[start:] + cycle[:start]
    raise ValueError(" -> ".join(cycle + [cycle[0]]))
'''

ORDER_VISIBLE = suite("from solution import install_order", "TestInstallOrder", '''    def test_chain(self):
        self.assertEqual(install_order({"app": ["lib"], "lib": ["core"], "core": []}), ["core", "lib", "app"])

    def test_no_dependencies(self):
        self.assertEqual(install_order({"only": []}), ["only"])
''')

ORDER_HIDDEN = suite("from solution import install_order", "TestInstallOrderRules", '''    def test_alphabetical_among_ready(self):
        self.assertEqual(install_order({"c": [], "a": [], "b": []}), ["a", "b", "c"])
        self.assertEqual(install_order({"z": [], "a": ["z"], "m": []}), ["m", "z", "a"])

    def test_ready_order_is_decided_at_each_step(self):
        packages = {"a": ["d"], "b": [], "c": ["b"], "d": []}
        self.assertEqual(install_order(packages), ["b", "c", "d", "a"])

    def test_diamond(self):
        packages = {"top": ["left", "right"], "left": ["base"], "right": ["base"], "base": []}
        self.assertEqual(install_order(packages), ["base", "left", "right", "top"])

    def test_duplicate_dependencies(self):
        self.assertEqual(install_order({"a": ["b", "b"], "b": []}), ["b", "a"])

    def test_empty(self):
        self.assertEqual(install_order({}), [])

    def test_missing_dependency(self):
        with self.assertRaises(KeyError):
            install_order({"a": ["ghost"]})

    def test_self_dependency(self):
        with self.assertRaises(ValueError) as caught:
            install_order({"a": ["a"]})
        self.assertEqual(str(caught.exception), "a -> a")

    def test_cycle_message(self):
        with self.assertRaises(ValueError) as caught:
            install_order({"c": ["a"], "a": ["b"], "b": ["c"]})
        self.assertEqual(str(caught.exception), "a -> b -> c -> a")

    def test_cycle_message_starts_at_smallest_name(self):
        with self.assertRaises(ValueError) as caught:
            install_order({"x": ["m"], "m": ["x"], "free": []})
        self.assertEqual(str(caught.exception), "m -> x -> m")

    def test_cycle_with_tail(self):
        packages = {"app": ["b"], "b": ["c"], "c": ["b"], "ok": []}
        with self.assertRaises(ValueError) as caught:
            install_order(packages)
        self.assertEqual(str(caught.exception), "b -> c -> b")

    def test_input_is_not_modified(self):
        packages = {"a": ["b", "b"], "b": []}
        install_order(packages)
        self.assertEqual(packages, {"a": ["b", "b"], "b": []})
''')

# --------------------------------------------------------------------------- #
# roman numerals
# --------------------------------------------------------------------------- #

ROMAN_PROMPT = (
    "Implement `to_roman(number)` and `from_roman(text)` in solution.py. `to_roman` converts an int from 1 to "
    "3999 into its standard upper-case Roman numeral (subtractive forms IV, IX, XL, XC, CD, CM). It raises "
    "ValueError outside that range and TypeError when the argument is not an int (bool is rejected too). "
    "`from_roman` accepts exactly the strings `to_roman` can produce and returns the int; every other string "
    "raises ValueError, including the empty string, lower case, surrounding spaces and non-standard forms such "
    "as IIII, VV, IL, IC, XM, IXI or MMMM."
)

ROMAN_SOLUTION = '''"""Strict Roman numeral conversion."""

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
'''

ROMAN_VISIBLE = suite("from solution import from_roman, to_roman", "TestRoman", '''    def test_to_roman(self):
        self.assertEqual(to_roman(14), "XIV")
        self.assertEqual(to_roman(2024), "MMXXIV")

    def test_from_roman(self):
        self.assertEqual(from_roman("XIV"), 14)
''')

ROMAN_HIDDEN = suite("from solution import from_roman, to_roman", "TestRomanRules", '''    def test_subtractive_forms(self):
        expected = {4: "IV", 9: "IX", 40: "XL", 90: "XC", 400: "CD", 900: "CM", 1994: "MCMXCIV", 3999: "MMMCMXCIX",
                    1: "I", 3888: "MMMDCCCLXXXVIII"}
        for number, text in expected.items():
            self.assertEqual(to_roman(number), text)
            self.assertEqual(from_roman(text), number)

    def test_round_trip_everything(self):
        for number in range(1, 4000):
            self.assertEqual(from_roman(to_roman(number)), number)

    def test_to_roman_range(self):
        for number in (0, -1, 4000):
            with self.assertRaises(ValueError, msg=str(number)):
                to_roman(number)

    def test_to_roman_types(self):
        for value in (1.0, "1", True, None):
            with self.assertRaises(TypeError, msg=repr(value)):
                to_roman(value)

    def test_from_roman_rejects_non_standard_forms(self):
        for text in ("IIII", "VV", "IL", "IC", "XM", "IXI", "MMMM", "VX", "LL", "DD", "XXXX", "CCCC",
                     "IVI", "IXIV", "XCX", "CMC", "IIV", "XIIX", "MCMC"):
            with self.assertRaises(ValueError, msg=text):
                from_roman(text)

    def test_from_roman_rejects_other_strings(self):
        for text in ("", "xiv", " XIV", "XIV ", "X IV", "ABC", "14", "N"):
            with self.assertRaises(ValueError, msg=repr(text)):
                from_roman(text)
''')

# --------------------------------------------------------------------------- #
# decimal rounding
# --------------------------------------------------------------------------- #

ROUND_PROMPT = (
    "Implement `round_decimal(text, places)` in solution.py: round a decimal number given as a string to "
    "`places` digits after the point using round-half-to-even, exactly, for inputs of any length (the result "
    "must not depend on binary floating point). Input syntax: an optional `-`, one or more digits, and "
    "optionally a `.` followed by one or more digits. Output: the same syntax with exactly `places` fraction "
    "digits (no point at all when `places` is 0), no leading zeros other than a single zero before the point, "
    "and no minus sign when the rounded value is zero. `places` is an int of at least 0; raise ValueError when "
    "it is negative. Raise ValueError for malformed input such as the empty string, `+1`, `.5`, `5.`, `1e3`, "
    "`1,5` or anything with spaces."
)

ROUND_SOLUTION = '''"""Exact half-even rounding of decimal strings."""

import re
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

_NUMBER = re.compile(r"-?[0-9]+(?:\\.[0-9]+)?")


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
'''

ROUND_VISIBLE = suite("from solution import round_decimal", "TestRoundDecimal", '''    def test_round_down(self):
        self.assertEqual(round_decimal("3.14159", 2), "3.14")

    def test_round_up(self):
        self.assertEqual(round_decimal("2.718", 2), "2.72")

    def test_pad(self):
        self.assertEqual(round_decimal("5", 2), "5.00")
''')

ROUND_HIDDEN = suite("from solution import round_decimal", "TestRoundDecimalRules", '''    def test_half_goes_to_even(self):
        self.assertEqual(round_decimal("2.5", 0), "2")
        self.assertEqual(round_decimal("3.5", 0), "4")
        self.assertEqual(round_decimal("0.125", 2), "0.12")
        self.assertEqual(round_decimal("0.135", 2), "0.14")
        self.assertEqual(round_decimal("1.005", 2), "1.00")
        self.assertEqual(round_decimal("2.675", 2), "2.68")

    def test_more_than_half_rounds_up(self):
        self.assertEqual(round_decimal("2.5000001", 0), "3")
        self.assertEqual(round_decimal("0.1250001", 2), "0.13")

    def test_carry(self):
        self.assertEqual(round_decimal("9.995", 2), "10.00")
        self.assertEqual(round_decimal("99.5", 0), "100")
        self.assertEqual(round_decimal("0.999", 2), "1.00")

    def test_negative_numbers(self):
        self.assertEqual(round_decimal("-1.5", 0), "-2")
        self.assertEqual(round_decimal("-2.5", 0), "-2")
        self.assertEqual(round_decimal("-3.14159", 3), "-3.142")

    def test_zero_has_no_sign(self):
        self.assertEqual(round_decimal("-0.004", 2), "0.00")
        self.assertEqual(round_decimal("-0.5", 0), "0")
        self.assertEqual(round_decimal("-0", 1), "0.0")
        self.assertEqual(round_decimal("0.5", 0), "0")

    def test_leading_zeros_are_dropped(self):
        self.assertEqual(round_decimal("007.50", 1), "7.5")
        self.assertEqual(round_decimal("000", 0), "0")
        self.assertEqual(round_decimal("00.25", 1), "0.2")

    def test_padding_and_places_zero(self):
        self.assertEqual(round_decimal("1.5", 4), "1.5000")
        self.assertEqual(round_decimal("12", 0), "12")
        self.assertEqual(round_decimal("12.4", 0), "12")

    def test_long_inputs_are_exact(self):
        self.assertEqual(round_decimal("123456789012345678901234567890.5", 0), "123456789012345678901234567890")
        self.assertEqual(round_decimal("123456789012345678901234567891.5", 0), "123456789012345678901234567892")
        self.assertEqual(round_decimal("0.0000000000000000000000015", 24), "0.000000000000000000000002")
        self.assertEqual(round_decimal("0.1234567890123456789012345", 24), "0.123456789012345678901234")

    def test_malformed_input(self):
        for text in ("", "+1", ".5", "5.", "1e3", "1,5", " 1", "1 ", "--1", "1.2.3", "abc", "-"):
            with self.assertRaises(ValueError, msg=repr(text)):
                round_decimal(text, 2)

    def test_negative_places(self):
        with self.assertRaises(ValueError):
            round_decimal("1.5", -1)
''')


def tasks() -> list:
    return [
        hard_task("py-hard-duration", DURATION_PROMPT, DURATION_SOLUTION, DURATION_VISIBLE, DURATION_HIDDEN,
                  ["units must be in descending order and unique", "format output is canonical", "bool is not an int here"]),
        hard_task("py-hard-allocate", ALLOCATE_PROMPT, ALLOCATE_SOLUTION, ALLOCATE_VISIBLE, ALLOCATE_HIDDEN,
                  ["parts sum exactly to the total", "leftover cents go to the largest remainders, earlier position first",
                   "negative totals mirror the positive allocation", "exact for arbitrarily large integers"]),
        hard_task("py-hard-ranges", RANGES_PROMPT, RANGES_SOLUTION, RANGES_VISIBLE, RANGES_HIDDEN,
                  ["only runs of three or more are hyphenated", "negative numbers round-trip", "expand validates every item"]),
        hard_task("py-hard-semver", SEMVER_PROMPT, SEMVER_SOLUTION, SEMVER_VISIBLE, SEMVER_HIDDEN,
                  ["caret follows the left-most non-zero component", "partial versions are padded with zeros",
                   "a malformed spec raises even when another alternative matches"]),
        hard_task("py-hard-expr", EXPR_PROMPT, EXPR_SOLUTION, EXPR_VISIBLE, EXPR_HIDDEN,
                  ["-2**2 is -4 and ** is right-associative", "floor semantics for // and %",
                   "every listed syntax error raises ValueError", "eval and exec are not called"]),
        hard_task("py-hard-wrap", WRAP_PROMPT, WRAP_SOLUTION, WRAP_VISIBLE, WRAP_HIDDEN,
                  ["paragraphs are separated by exactly one empty string", "over-long words are cut into width-sized chunks",
                   "no line has leading or trailing spaces"]),
        hard_task("py-hard-intervals", INTERVALS_PROMPT, INTERVALS_SOLUTION, INTERVALS_VISIBLE, INTERVALS_HIDDEN,
                  ["touching intervals merge", "removing from the middle splits an interval", "len counts stored integers"]),
        hard_task("py-hard-table", TABLE_PROMPT, TABLE_SOLUTION, TABLE_VISIBLE, TABLE_HIDDEN,
                  ["numbers align right, everything else left", "floats have two decimals", "no trailing spaces on any line"]),
        hard_task("py-hard-template", TEMPLATE_PROMPT, TEMPLATE_SOLUTION, TEMPLATE_VISIBLE, TEMPLATE_HIDDEN,
                  ["doubled braces are literals", "filters apply left to right to the string value",
                   "missing names raise KeyError, malformed templates raise ValueError"]),
        hard_task("py-hard-order", ORDER_PROMPT, ORDER_SOLUTION, ORDER_VISIBLE, ORDER_HIDDEN,
                  ["alphabetically smallest ready package first", "cycle message starts at the smallest name in the cycle",
                   "the input is not modified"]),
        hard_task("py-hard-roman", ROMAN_PROMPT, ROMAN_SOLUTION, ROMAN_VISIBLE, ROMAN_HIDDEN,
                  ["only standard numerals are accepted", "range is 1 to 3999", "bool is not an int here"]),
        hard_task("py-hard-round", ROUND_PROMPT, ROUND_SOLUTION, ROUND_VISIBLE, ROUND_HIDDEN,
                  ["ties go to the even digit", "exact for inputs of any length", "zero is written without a minus sign"]),
    ]
