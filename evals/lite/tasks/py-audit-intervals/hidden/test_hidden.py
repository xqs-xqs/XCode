import unittest

from solution import IntervalSet


class TestIntervalSetRules(unittest.TestCase):
    def build(self, *pairs):
        items = IntervalSet()
        for start, end in pairs:
            items.add(start, end)
        return items

    def test_touching_intervals_merge(self):
        self.assertEqual(self.build((1, 3), (3, 5)).intervals(), [(1, 5)])
        self.assertEqual(self.build((3, 5), (1, 3)).intervals(), [(1, 5)])

    def test_overlapping_and_contained(self):
        self.assertEqual(self.build((1, 5), (3, 8)).intervals(), [(1, 8)])
        self.assertEqual(self.build((1, 10), (3, 4)).intervals(), [(1, 10)])
        self.assertEqual(self.build((3, 4), (1, 10)).intervals(), [(1, 10)])

    def test_add_bridges_several(self):
        self.assertEqual(self.build((1, 2), (4, 5), (7, 8), (2, 7)).intervals(), [(1, 8)])
        self.assertEqual(self.build((1, 2), (4, 5), (7, 8), (3, 6)).intervals(), [(1, 2), (3, 6), (7, 8)])

    def test_gap_of_one_does_not_merge(self):
        self.assertEqual(self.build((1, 3), (4, 6)).intervals(), [(1, 3), (4, 6)])

    def test_remove_splits(self):
        items = self.build((1, 10))
        items.remove(4, 6)
        self.assertEqual(items.intervals(), [(1, 4), (6, 10)])
        self.assertFalse(items.contains(4))
        self.assertFalse(items.contains(5))
        self.assertTrue(items.contains(6))

    def test_remove_edges_and_whole(self):
        items = self.build((1, 10))
        items.remove(0, 3)
        items.remove(8, 20)
        self.assertEqual(items.intervals(), [(3, 8)])
        items.remove(3, 8)
        self.assertEqual(items.intervals(), [])

    def test_remove_across_several(self):
        items = self.build((1, 3), (5, 7), (9, 11))
        items.remove(2, 10)
        self.assertEqual(items.intervals(), [(1, 2), (10, 11)])

    def test_remove_nothing(self):
        items = self.build((1, 3))
        items.remove(3, 5)
        items.remove(-5, 1)
        self.assertEqual(items.intervals(), [(1, 3)])

    def test_len(self):
        items = self.build((1, 4), (10, 12))
        self.assertEqual(len(items), 5)
        items.remove(2, 3)
        self.assertEqual(len(items), 4)
        self.assertEqual(len(IntervalSet()), 0)

    def test_empty_interval_is_a_no_op(self):
        items = self.build((1, 3))
        items.add(7, 7)
        items.remove(2, 2)
        self.assertEqual(items.intervals(), [(1, 3)])

    def test_reversed_bounds_raise(self):
        items = IntervalSet()
        with self.assertRaises(ValueError):
            items.add(5, 3)
        with self.assertRaises(ValueError):
            items.remove(5, 3)

    def test_negative_numbers(self):
        items = self.build((-5, -1), (-1, 2))
        self.assertEqual(items.intervals(), [(-5, 2)])
        self.assertTrue(items.contains(-5))
        self.assertFalse(items.contains(2))


if __name__ == "__main__":
    unittest.main()
