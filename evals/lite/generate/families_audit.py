"""Audit tasks: a module with several seeded defects, of which one is reported.

Implement-from-spec tasks are solved by a single agent every time, so they
cannot separate collaboration topologies. These tasks model a different and
common situation: a bug report names one symptom, the visible tests cover that
symptom and the ordinary path, and the module has further deviations from its
specification that nothing visible exercises. An agent that stops when the
visible suite is green has not finished.

Each task reuses a module from the spec-heavy family. The starter is the
reference solution with three or four small defects applied; the prompt gives
the full specification and the one reported symptom; the hidden suite is the
spec-heavy family's hidden suite, unchanged. Every defect is caught by that
hidden suite on its own (checked by `check_defects`).

The family was written and calibrated before any model saw it.
"""

from __future__ import annotations

import families_hard as hard
from families_python import py_task

AUDIT = "audit"


def seeded(solution: str, defects: list) -> str:
    """Apply (good, bad) replacements; each good snippet must occur exactly once."""
    code = solution
    for good, bad in defects:
        if solution.count(good) != 1:
            raise ValueError(f"defect anchor must occur exactly once: {good!r}")
        code = code.replace(good, bad)
    return code


def with_reported_test(visible: str, test: str) -> str:
    """Add the reported symptom to the visible suite as one more test method."""
    marker = "\nif __name__ == \"__main__\":"
    head, tail = visible.split(marker)
    return head.rstrip("\n") + "\n\n" + test.rstrip("\n") + "\n\n" + marker + tail


def audit_task(id, spec, solution, visible, hidden, defects, symptom, reported_test, acceptance):
    prompt = (
        "solution.py is meant to implement the specification below, but it contains several defects. One has been "
        f"reported: {symptom} Fix that and every other deviation from the specification. Keep the public names and "
        "signatures unchanged and do not change behaviour the specification requires.\n\nSpecification: " + spec
    )
    task = py_task(id, AUDIT, prompt, seeded(solution, defects), solution,
                   with_reported_test(visible, reported_test), hidden, acceptance, tags=("audit", "seeded-defects"))
    task["defects"] = defects
    return task


DURATION_DEFECTS = [
    ("        if index is None or index < next_unit:", "        if index is None:"),
    ('    if seconds == 0:\n        return "0s"\n', ""),
    ("    if isinstance(seconds, bool) or not isinstance(seconds, int):", "    if not isinstance(seconds, int):"),
    ("if unit == match.group(2)), None)", "if unit == match.group(2).lower()), None)"),
]
DURATION_REPORTED = '''    def test_reported_out_of_order_units(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")
'''

ALLOCATE_DEFECTS = [
    ("key=lambda index: (-remainders[index], index))", "key=lambda index: (-remainders[index], -index))"),
    ("    return [-part for part in parts] if total < 0 else parts", "    return parts"),
    ("    if isinstance(total, bool) or not isinstance(total, int):", "    if not isinstance(total, int):"),
    ('    if scale == 0:\n        raise ValueError("at least one weight must be positive")',
     "    if scale == 0:\n        return [0] * len(weights)"),
]
ALLOCATE_REPORTED = '''    def test_reported_tie_goes_to_earlier_position(self):
        self.assertEqual(allocate(100, [1, 1, 1]), [34, 33, 33])
'''

RANGES_DEFECTS = [
    ("        if end - index >= 2:", "        if end - index >= 1:"),
    ('        if last < first:\n            raise ValueError(f"descending range {item!r}")\n', ""),
    ("    if not text.strip():\n        return []", "    if not text:\n        return []"),
    ("    values = sorted(set(numbers))", "    values = sorted(numbers)"),
]
RANGES_REPORTED = '''    def test_reported_pair_is_not_a_range(self):
        self.assertEqual(compress([1, 2, 4, 5, 6]), "1,2,4-6")
'''

SEMVER_DEFECTS = [
    ("        if major > 0:\n            upper = (major + 1, 0, 0)\n        elif minor > 0:\n            upper = (0, minor + 1, 0)\n"
     "        else:\n            upper = (0, 0, patch + 1)\n",
     "        upper = (major + 1, 0, 0)\n"),
    ("        upper = (base[0], base[1] + 1, 0)", "        upper = (base[0] + 1, 0, 0)"),
    ('_NUMBER = r"(?:0|[1-9][0-9]*)"', '_NUMBER = r"[0-9]+"'),
    ("        return lambda version: version <= base", "        return lambda version: version < base"),
]
SEMVER_REPORTED = '''    def test_reported_caret_with_zero_major(self):
        self.assertFalse(satisfies("0.3.0", "^0.2.3"))
'''

EXPR_DEFECTS = [
    ("                value %= right", "                value = int(math.fmod(value, right))"),
    ("                value //= right", "                value = int(value / right)"),
    ('            if exponent < 0:\n                raise ValueError("negative exponent")\n', ""),
    ('    if parser.peek() is not None:\n        raise ValueError(f"unexpected token {parser.peek()!r}")\n', ""),
    ("import re\n", "import math\nimport re\n"),
]
EXPR_REPORTED = '''    def test_reported_modulo_of_negative(self):
        self.assertEqual(evaluate("-7 % 3"), 2)
'''

WRAP_DEFECTS = [
    ("            elif len(line) + 1 + len(word) <= width:", "            elif len(line) + 1 + len(word) < width:"),
    ('        if number:\n            lines.append("")\n', ""),
    ("                lines.extend(chunks[:-1])\n                line = chunks[-1]",
     '                lines.extend(chunks)\n                line = ""'),
]
WRAP_REPORTED = '''    def test_reported_exact_fit(self):
        self.assertEqual(wrap("a b c", 3), ["a b", "c"])
'''

INTERVALS_DEFECTS = [
    ("            if high < start:", "            if high <= start:"),
    ("            if end < high:\n                kept.append((end, high))", "            elif end < high:\n                kept.append((end, high))"),
    ("        return sum(high - low for low, high in self._items)", "        return len(self._items)"),
    ("        if start == end:\n            return\n        merged, placed = [], False", "        merged, placed = [], False"),
]
INTERVALS_REPORTED = '''    def test_reported_touching_intervals_merge(self):
        items = IntervalSet()
        items.add(1, 3)
        items.add(3, 5)
        self.assertEqual(items.intervals(), [(1, 5)])
'''

TABLE_DEFECTS = [
    ("    return isinstance(cell, (int, float)) and not isinstance(cell, bool)", "    return isinstance(cell, (int, float))"),
    ('    return "\\n".join(line.rstrip() for line in lines)', '    return "\\n".join(lines)'),
    ('        if len(row) > len(headers):\n            raise ValueError("row has more cells than headers")\n', ""),
    ('        return f"{cell:.2f}"', "        return str(round(cell, 2))"),
]
TABLE_REPORTED = '''    def test_reported_booleans_align_left(self):
        text = format_table(["ok", "qty"], [[True, 1], [False, 22]])
        self.assertEqual(text, "ok   qty\\n---  ---\\nyes    1\\nno    22")
'''

TEMPLATE_DEFECTS = [
    ("    text = str(current)\n    for filter_name in filters:", "    text = str(current)\n    for filter_name in reversed(filters):"),
    ('            if not template.startswith("}}", index):\n                raise ValueError("unmatched }")\n'
     '            output.append("}")\n            index += 2',
     '            output.append("}")\n            index += 2 if template.startswith("}}", index) else 1'),
    ("        if not isinstance(current, dict):\n            raise KeyError(segment)\n", ""),
    ('    name, *filters = [piece.strip() for piece in inner.split("|")]', '    name, *filters = inner.split("|")'),
]
TEMPLATE_REPORTED = '''    def test_reported_filter_order(self):
        self.assertEqual(render("{v|upper|lower}", {"v": "Ab"}), "ab")
'''

ORDER_DEFECTS = [
    ("        name = heapq.heappop(ready)", "        name = ready.pop()"),
    ("        dependencies[name] = set(needs)", "        dependencies[name] = set(needs) - {name}"),
    ('    raise ValueError(" -> ".join(cycle + [cycle[0]]))', '    raise ValueError(" -> ".join(cycle))'),
]
ORDER_REPORTED = '''    def test_reported_alphabetical_order(self):
        self.assertEqual(install_order({"c": [], "a": [], "b": []}), ["a", "b", "c"])
'''

ROMAN_DEFECTS = [
    ("    if position != len(text) or not 1 <= total <= 3999 or to_roman(total) != text:",
     "    if position != len(text) or not 1 <= total <= 3999:"),
    ('    if not 1 <= number <= 3999:\n        raise ValueError("number out of range")',
     '    if not 1 <= number <= 4999:\n        raise ValueError("number out of range")'),
    ("    if isinstance(number, bool) or not isinstance(number, int):", "    if not isinstance(number, int):"),
]
ROMAN_REPORTED = '''    def test_reported_non_standard_numeral(self):
        with self.assertRaises(ValueError):
            from_roman("IIII")
'''

ROUND_DEFECTS = [
    ("rounding=ROUND_HALF_EVEN)", "rounding=ROUND_HALF_UP)"),
    ("from decimal import ROUND_HALF_EVEN, Decimal, localcontext", "from decimal import ROUND_HALF_UP, Decimal, localcontext"),
    ('    return rendered.lstrip("-") if value == 0 else rendered', "    return rendered"),
    ("        context.prec = len(text) + places + 5\n", ""),
    ('_NUMBER = re.compile(r"-?[0-9]+(?:\\.[0-9]+)?")', '_NUMBER = re.compile(r"[-+]?[0-9]+(?:\\.[0-9]+)?")'),
]
ROUND_REPORTED = '''    def test_reported_half_goes_to_even(self):
        self.assertEqual(round_decimal("2.5", 0), "2")
'''


def tasks() -> list:
    return [
        audit_task("py-audit-duration", hard.DURATION_PROMPT, hard.DURATION_SOLUTION, hard.DURATION_VISIBLE,
                   hard.DURATION_HIDDEN, DURATION_DEFECTS,
                   '`parse_duration("30m1h")` returns 5400 instead of raising ValueError.', DURATION_REPORTED,
                   ["units must be in descending order and unique", "format output is canonical", "bool is not an int here"]),
        audit_task("py-audit-allocate", hard.ALLOCATE_PROMPT, hard.ALLOCATE_SOLUTION, hard.ALLOCATE_VISIBLE,
                   hard.ALLOCATE_HIDDEN, ALLOCATE_DEFECTS,
                   "`allocate(100, [1, 1, 1])` returns [33, 33, 34] instead of [34, 33, 33].", ALLOCATE_REPORTED,
                   ["parts sum exactly to the total", "leftover cents go to the largest remainders, earlier position first",
                    "negative totals mirror the positive allocation", "invalid weights raise the documented errors"]),
        audit_task("py-audit-ranges", hard.RANGES_PROMPT, hard.RANGES_SOLUTION, hard.RANGES_VISIBLE,
                   hard.RANGES_HIDDEN, RANGES_DEFECTS,
                   '`compress([1, 2, 4, 5, 6])` returns "1-2,4-6" instead of "1,2,4-6".', RANGES_REPORTED,
                   ["only runs of three or more are hyphenated", "duplicates are removed", "expand validates every item"]),
        audit_task("py-audit-semver", hard.SEMVER_PROMPT, hard.SEMVER_SOLUTION, hard.SEMVER_VISIBLE,
                   hard.SEMVER_HIDDEN, SEMVER_DEFECTS,
                   '`satisfies("0.3.0", "^0.2.3")` returns True instead of False.', SEMVER_REPORTED,
                   ["caret follows the left-most non-zero component", "tilde stays within the minor version",
                    "leading zeros are rejected", "every comparator compares as documented"]),
        audit_task("py-audit-expr", hard.EXPR_PROMPT, hard.EXPR_SOLUTION, hard.EXPR_VISIBLE,
                   hard.EXPR_HIDDEN, EXPR_DEFECTS[:1] + EXPR_DEFECTS[4:] + EXPR_DEFECTS[1:4],
                   '`evaluate("-7 % 3")` returns -1 instead of 2.', EXPR_REPORTED,
                   ["floor semantics for // and %", "a negative exponent raises ValueError",
                    "every listed syntax error raises ValueError", "eval and exec are not called"]),
        audit_task("py-audit-wrap", hard.WRAP_PROMPT, hard.WRAP_SOLUTION, hard.WRAP_VISIBLE,
                   hard.WRAP_HIDDEN, WRAP_DEFECTS,
                   '`wrap("a b c", 3)` returns ["a", "b", "c"] instead of ["a b", "c"].', WRAP_REPORTED,
                   ["a word that exactly fits stays on the line", "paragraphs are separated by exactly one empty string",
                    "the word after an over-long word may join its last chunk"]),
        audit_task("py-audit-intervals", hard.INTERVALS_PROMPT, hard.INTERVALS_SOLUTION, hard.INTERVALS_VISIBLE,
                   hard.INTERVALS_HIDDEN, INTERVALS_DEFECTS,
                   "after `add(1, 3)` and `add(3, 5)`, `intervals()` returns two intervals instead of [(1, 5)].",
                   INTERVALS_REPORTED,
                   ["touching intervals merge", "removing from the middle splits an interval",
                    "len counts stored integers", "an empty interval is a no-op"]),
        audit_task("py-audit-table", hard.TABLE_PROMPT, hard.TABLE_SOLUTION, hard.TABLE_VISIBLE,
                   hard.TABLE_HIDDEN, TABLE_DEFECTS,
                   "a column of booleans is right-aligned instead of left-aligned.", TABLE_REPORTED,
                   ["numbers align right, everything else left", "floats have two decimals",
                    "no trailing spaces on any line", "over-long rows raise ValueError"]),
        audit_task("py-audit-template", hard.TEMPLATE_PROMPT, hard.TEMPLATE_SOLUTION, hard.TEMPLATE_VISIBLE,
                   hard.TEMPLATE_HIDDEN, TEMPLATE_DEFECTS,
                   '`render("{v|upper|lower}", {"v": "Ab"})` returns "AB" instead of "ab".', TEMPLATE_REPORTED,
                   ["filters apply left to right", "a lone closing brace is an error",
                    "walking into a non-dict raises KeyError", "whitespace inside a placeholder is ignored"]),
        audit_task("py-audit-order", hard.ORDER_PROMPT, hard.ORDER_SOLUTION, hard.ORDER_VISIBLE,
                   hard.ORDER_HIDDEN, ORDER_DEFECTS,
                   '`install_order({"c": [], "a": [], "b": []})` does not return ["a", "b", "c"].', ORDER_REPORTED,
                   ["alphabetically smallest ready package first", "a self-dependency is a cycle",
                    "the cycle message ends with the name it starts with"]),
        audit_task("py-audit-roman", hard.ROMAN_PROMPT, hard.ROMAN_SOLUTION, hard.ROMAN_VISIBLE,
                   hard.ROMAN_HIDDEN, ROMAN_DEFECTS,
                   '`from_roman("IIII")` returns 4 instead of raising ValueError.', ROMAN_REPORTED,
                   ["only standard numerals are accepted", "range is 1 to 3999", "bool is not an int here"]),
        audit_task("py-audit-round", hard.ROUND_PROMPT, hard.ROUND_SOLUTION, hard.ROUND_VISIBLE,
                   hard.ROUND_HIDDEN, ROUND_DEFECTS[:2] + ROUND_DEFECTS[2:],
                   '`round_decimal("2.5", 0)` returns "3" instead of "2".', ROUND_REPORTED,
                   ["ties go to the even digit", "exact for inputs of any length",
                    "zero is written without a minus sign", "a leading plus sign is rejected"]),
    ]


def check_defects() -> list:
    """Verify each seeded defect on its own fails the hidden suite, and that
    fixing only the reported defect leaves the visible suite green while the
    hidden suite still fails. Returns a list of problems (empty when sound)."""
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    def run(code: str, files: dict, names: list) -> bool:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "solution.py").write_text(code, encoding="utf-8")
            for name, content in files.items():
                (root / name).write_text(content, encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "unittest", *names], cwd=root,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            return result.returncode == 0

    problems = []
    for task in tasks():
        solution = task["solution"]["solution.py"]
        hidden = task["hidden"]
        visible = {"test_visible.py": task["starter"]["test_visible.py"]}
        defects = task["defects"]
        groups = _defect_groups(task["id"], defects)
        for label, group in groups.items():
            if run(seeded(solution, group), hidden, ["test_visible.py", "test_hidden.py"]):
                problems.append(f"{task['id']}: defect {label} alone is not caught by the hidden suite")
        rest = [pair for label, group in groups.items() if label != "reported" for pair in group]
        partly_fixed = seeded(solution, rest)
        if not run(partly_fixed, visible, ["test_visible.py"]):
            problems.append(f"{task['id']}: visible suite fails after fixing only the reported defect")
        if run(partly_fixed, hidden, ["test_visible.py", "test_hidden.py"]):
            problems.append(f"{task['id']}: hidden suite passes after fixing only the reported defect")
        if run(task["starter"]["solution.py"], visible, ["test_visible.py"]):
            problems.append(f"{task['id']}: the reported defect is not exposed by the visible suite")
    return problems


def _defect_groups(task_id: str, defects: list) -> dict:
    """Group replacements that form one defect (an import that a defect needs)."""
    if task_id == "py-audit-expr":  # reported defect needs `import math`
        return {"reported": defects[:2], "d2": defects[2:3], "d3": defects[3:4], "d4": defects[4:5]}
    if task_id == "py-audit-round":  # reported defect changes the import and the call
        return {"reported": defects[:2], "d2": defects[2:3], "d3": defects[3:4], "d4": defects[4:5]}
    groups = {"reported": defects[:1]}
    for number, pair in enumerate(defects[1:], 2):
        groups[f"d{number}"] = [pair]
    return groups


if __name__ == "__main__":
    found = check_defects()
    for line in found:
        print(line)
    print(f"{len(tasks())} audit tasks, {sum(len(_defect_groups(t['id'], t['defects'])) for t in tasks())} defects, "
          f"{len(found)} problem(s)")
    raise SystemExit(1 if found else 0)
