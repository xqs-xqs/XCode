import unittest

from solution import wrap


class TestWrap(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(wrap("the quick brown fox", 10), ["the quick", "brown fox"])

    def test_short_text(self):
        self.assertEqual(wrap("hi", 10), ["hi"])

    def test_reported_exact_fit(self):
        self.assertEqual(wrap("a b c", 3), ["a b", "c"])


if __name__ == "__main__":
    unittest.main()
