import unittest

from solution import format_table


class TestFormatTable(unittest.TestCase):
    def test_strings(self):
        text = format_table(["name", "city"], [["Ann", "Oslo"], ["Robert", "Rome"]])
        self.assertEqual(text, "name    city\n------  ----\nAnn     Oslo\nRobert  Rome")

    def test_numbers_align_right(self):
        text = format_table(["item", "qty"], [["nut", 5], ["bolt", 120]])
        self.assertEqual(text, "item  qty\n----  ---\nnut     5\nbolt  120")

    def test_reported_booleans_align_left(self):
        text = format_table(["ok", "qty"], [[True, 1], [False, 22]])
        self.assertEqual(text, "ok   qty\n---  ---\nyes    1\nno    22")


if __name__ == "__main__":
    unittest.main()
