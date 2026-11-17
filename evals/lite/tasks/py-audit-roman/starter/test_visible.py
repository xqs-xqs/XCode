import unittest

from solution import from_roman, to_roman


class TestRoman(unittest.TestCase):
    def test_to_roman(self):
        self.assertEqual(to_roman(14), "XIV")
        self.assertEqual(to_roman(2024), "MMXXIV")

    def test_from_roman(self):
        self.assertEqual(from_roman("XIV"), 14)

    def test_reported_non_standard_numeral(self):
        with self.assertRaises(ValueError):
            from_roman("IIII")


if __name__ == "__main__":
    unittest.main()
