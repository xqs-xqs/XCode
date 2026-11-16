import unittest

from solution import format_table


class TestFormatTableRules(unittest.TestCase):
    def test_floats_have_two_decimals(self):
        text = format_table(["v"], [[1.0], [2.25], [10.5]])
        self.assertEqual(text, "v\n-----\n 1.00\n 2.25\n10.50")

    def test_none_and_bool(self):
        text = format_table(["a", "ok"], [[None, True], ["x", False]])
        self.assertEqual(text, "a  ok\n-  ---\n   yes\nx  no")

    def test_bool_is_left_aligned(self):
        text = format_table(["enabled"], [[True], [False]])
        self.assertEqual(text, "enabled\n-------\nyes\nno")

    def test_header_wider_than_cells(self):
        text = format_table(["quantity"], [[1], [22]])
        self.assertEqual(text, "quantity\n--------\n       1\n      22")

    def test_trailing_spaces_removed(self):
        text = format_table(["a", "b"], [["long text", None], ["x", "y"]])
        self.assertEqual(text, "a          b\n---------  -\nlong text\nx          y")
        for line in text.split("\n"):
            self.assertEqual(line, line.rstrip())

    def test_short_row_is_padded(self):
        text = format_table(["a", "b", "c"], [["x"], ["y", 2, 3]])
        self.assertEqual(text, "a  b  c\n-  -  -\nx\ny  2  3")

    def test_mixed_column(self):
        text = format_table(["value"], [["abc"], [7], [None], ["z"]])
        self.assertEqual(text, "value\n-----\nabc\n    7\n\nz")

    def test_negative_numbers(self):
        text = format_table(["n"], [[-5], [12], [-1.5]])
        self.assertEqual(text, "n\n-----\n   -5\n   12\n-1.50")

    def test_no_rows(self):
        self.assertEqual(format_table(["a", "bb"], []), "a  bb\n-  --")

    def test_no_trailing_newline(self):
        self.assertFalse(format_table(["a"], [["x"]]).endswith("\n"))

    def test_errors(self):
        with self.assertRaises(ValueError):
            format_table([], [])
        with self.assertRaises(ValueError):
            format_table(["a"], [["x", "y"]])


if __name__ == "__main__":
    unittest.main()
