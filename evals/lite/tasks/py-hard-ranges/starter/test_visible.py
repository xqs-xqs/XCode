import unittest

from solution import compress, expand


class TestRanges(unittest.TestCase):
    def test_compress(self):
        self.assertEqual(compress([1, 2, 3, 5]), "1-3,5")

    def test_expand(self):
        self.assertEqual(expand("1-3,5"), [1, 2, 3, 5])


if __name__ == "__main__":
    unittest.main()
