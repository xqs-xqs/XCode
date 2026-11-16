import unittest

from solution import IntervalSet


class TestIntervalSet(unittest.TestCase):
    def test_add_and_contains(self):
        items = IntervalSet()
        items.add(1, 4)
        self.assertTrue(items.contains(1))
        self.assertTrue(items.contains(3))
        self.assertFalse(items.contains(4))

    def test_two_separate_intervals(self):
        items = IntervalSet()
        items.add(5, 7)
        items.add(1, 3)
        self.assertEqual(items.intervals(), [(1, 3), (5, 7)])


if __name__ == "__main__":
    unittest.main()
