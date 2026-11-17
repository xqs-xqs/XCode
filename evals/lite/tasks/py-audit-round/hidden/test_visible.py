import unittest

from solution import round_decimal


class TestRoundDecimal(unittest.TestCase):
    def test_round_down(self):
        self.assertEqual(round_decimal("3.14159", 2), "3.14")

    def test_round_up(self):
        self.assertEqual(round_decimal("2.718", 2), "2.72")

    def test_pad(self):
        self.assertEqual(round_decimal("5", 2), "5.00")

    def test_reported_half_goes_to_even(self):
        self.assertEqual(round_decimal("2.5", 0), "2")


if __name__ == "__main__":
    unittest.main()
