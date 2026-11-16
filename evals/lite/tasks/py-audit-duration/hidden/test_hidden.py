import unittest

from solution import format_duration, parse_duration


class TestDurationRules(unittest.TestCase):
    def test_parse_all_units(self):
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


if __name__ == "__main__":
    unittest.main()
