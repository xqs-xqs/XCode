import unittest

from solution import evaluate


class TestEvaluate(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)

    def test_parentheses(self):
        self.assertEqual(evaluate("(1 + 2) * 3"), 9)

    def test_floor_division(self):
        self.assertEqual(evaluate("7 // 2"), 3)


if __name__ == "__main__":
    unittest.main()
