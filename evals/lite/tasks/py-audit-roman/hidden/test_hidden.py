import unittest

from solution import from_roman, to_roman


class TestRomanRules(unittest.TestCase):
    def test_subtractive_forms(self):
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


if __name__ == "__main__":
    unittest.main()
