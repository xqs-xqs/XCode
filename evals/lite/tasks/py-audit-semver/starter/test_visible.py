import unittest

from solution import satisfies


class TestSatisfies(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(satisfies("1.2.3", "1.2.3"))
        self.assertFalse(satisfies("1.2.4", "1.2.3"))

    def test_range(self):
        self.assertTrue(satisfies("1.5.0", ">=1.2.0 <2.0.0"))
        self.assertFalse(satisfies("2.0.0", ">=1.2.0 <2.0.0"))

    def test_caret(self):
        self.assertTrue(satisfies("1.9.9", "^1.2.3"))

    def test_reported_caret_with_zero_major(self):
        self.assertFalse(satisfies("0.3.0", "^0.2.3"))


if __name__ == "__main__":
    unittest.main()
