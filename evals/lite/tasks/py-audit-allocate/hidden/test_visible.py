import unittest

from solution import allocate


class TestAllocate(unittest.TestCase):
    def test_even_split(self):
        self.assertEqual(allocate(100, [1, 1]), [50, 50])

    def test_weighted_split(self):
        self.assertEqual(allocate(100, [1, 3]), [25, 75])

    def test_reported_tie_goes_to_earlier_position(self):
        self.assertEqual(allocate(100, [1, 1, 1]), [34, 33, 33])


if __name__ == "__main__":
    unittest.main()
