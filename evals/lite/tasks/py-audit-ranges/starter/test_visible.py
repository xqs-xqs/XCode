import unittest

from solution import compress, expand


class TestRanges(unittest.TestCase):
    def test_compress(self):
        self.assertEqual(compress([1, 2, 3, 5]), "1-3,5")

    def test_expand(self):
        self.assertEqual(expand("1-3,5"), [1, 2, 3, 5])

    def test_reported_pair_is_not_a_range(self):
        self.assertEqual(compress([1, 2, 4, 5, 6]), "1,2,4-6")


if __name__ == "__main__":
    unittest.main()
