import unittest

from solution import compress, expand


class TestRangeRules(unittest.TestCase):
    def test_compress_short_runs_stay_single(self):
        self.assertEqual(compress([1, 2, 3, 5, 7, 8]), "1-3,5,7,8")
        self.assertEqual(compress([1, 2, 4, 5, 6]), "1,2,4-6")
        self.assertEqual(compress([5]), "5")

    def test_compress_sorts_and_dedupes(self):
        self.assertEqual(compress([3, 1, 2, 2]), "1-3")
        self.assertEqual(compress([10, 9, 8, 8]), "8-10")
        self.assertEqual(compress(value for value in (4, 3, 2)), "2-4")

    def test_compress_negatives(self):
        self.assertEqual(compress([-3, -2, -1]), "-3--1")
        self.assertEqual(compress([-3, -2, -1, 0, 1]), "-3-1")
        self.assertEqual(compress([-2, -1]), "-2,-1")
        self.assertEqual(compress([-5, -3]), "-5,-3")

    def test_compress_empty(self):
        self.assertEqual(compress([]), "")

    def test_expand_lenient_syntax(self):
        self.assertEqual(expand(" 1 - 3 , 5 "), [1, 2, 3, 5])
        self.assertEqual(expand("4-4"), [4])
        self.assertEqual(expand("1-2"), [1, 2])

    def test_expand_order_and_overlap(self):
        self.assertEqual(expand("5,1-2,2-3"), [1, 2, 3, 5])
        self.assertEqual(expand("3,3,3"), [3])

    def test_expand_negatives(self):
        self.assertEqual(expand("-3--1"), [-3, -2, -1])
        self.assertEqual(expand("-3-1"), [-3, -2, -1, 0, 1])
        self.assertEqual(expand("-2,-1"), [-2, -1])

    def test_expand_empty(self):
        self.assertEqual(expand(""), [])
        self.assertEqual(expand("   "), [])

    def test_expand_errors(self):
        for text in ("5-3", "1,,2", ",1", "1,", "a", "1-2-3", "1.5", "1-", "1 2"):
            with self.assertRaises(ValueError, msg=text):
                expand(text)

    def test_round_trip(self):
        for values in ([1, 2, 3, 5, 7, 8], [-4, -3, -2, 0, 9], [100]):
            self.assertEqual(expand(compress(values)), values)


if __name__ == "__main__":
    unittest.main()
