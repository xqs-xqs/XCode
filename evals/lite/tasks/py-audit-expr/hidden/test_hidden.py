import unittest

import inspect
import re

import solution
from solution import evaluate


class TestEvaluateRules(unittest.TestCase):
    def test_power_and_unary_minus(self):
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
        self.assertIsNone(re.search(r"\b(eval|exec)\s*\(", source))


if __name__ == "__main__":
    unittest.main()
