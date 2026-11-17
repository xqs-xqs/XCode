import unittest

from solution import format_duration, parse_duration


class TestDuration(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("45s"), 45)

    def test_format(self):
        self.assertEqual(format_duration(5400), "1h30m")
        self.assertEqual(format_duration(45), "45s")


if __name__ == "__main__":
    unittest.main()
