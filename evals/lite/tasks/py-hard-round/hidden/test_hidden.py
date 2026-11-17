import unittest

from solution import round_decimal


class TestRoundDecimalRules(unittest.TestCase):
    def test_half_goes_to_even(self):
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


if __name__ == "__main__":
    unittest.main()
