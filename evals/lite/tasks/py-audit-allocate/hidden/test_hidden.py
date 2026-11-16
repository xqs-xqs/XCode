import unittest

from solution import allocate


class TestAllocateRules(unittest.TestCase):
    def test_leftover_goes_to_largest_remainder(self):
        self.assertEqual(allocate(100, [1, 2]), [33, 67])
        self.assertEqual(allocate(10, [1, 1, 4]), [2, 2, 6])

    def test_ties_go_to_earlier_position(self):
        self.assertEqual(allocate(100, [1, 1, 1]), [34, 33, 33])
        self.assertEqual(allocate(5, [1, 1]), [3, 2])
        self.assertEqual(allocate(1, [1, 1, 1, 1]), [1, 0, 0, 0])
        self.assertEqual(allocate(2, [1, 1, 1]), [1, 1, 0])

    def test_zero_weight_gets_nothing(self):
        self.assertEqual(allocate(10, [0, 1, 0]), [0, 10, 0])
        self.assertEqual(allocate(100, [1, 0, 1, 0, 1]), [34, 0, 33, 0, 33])

    def test_zero_total(self):
        self.assertEqual(allocate(0, [1, 2]), [0, 0])

    def test_negative_total(self):
        self.assertEqual(allocate(-100, [1, 1, 1]), [-34, -33, -33])
        self.assertEqual(allocate(-5, [1, 1]), [-3, -2])

    def test_exact_for_large_integers(self):
        self.assertEqual(allocate(10 ** 18 + 1, [1, 1]), [5 * 10 ** 17 + 1, 5 * 10 ** 17])
        self.assertEqual(allocate(10 ** 30, [1, 2]), [(10 ** 30) // 3, 10 ** 30 - (10 ** 30) // 3])

    def test_sum_is_preserved(self):
        for total in (1, 7, 99, 1001, -13):
            for weights in ([3, 5, 7], [1, 1, 1, 1, 1, 1, 1], [9, 1]):
                self.assertEqual(sum(allocate(total, weights)), total)

    def test_value_errors(self):
        for weights in ([], [0, 0], [1, -1]):
            with self.assertRaises(ValueError, msg=repr(weights)):
                allocate(10, weights)

    def test_type_errors(self):
        with self.assertRaises(TypeError):
            allocate(10.0, [1, 1])
        with self.assertRaises(TypeError):
            allocate(10, [1, 1.5])
        with self.assertRaises(TypeError):
            allocate(True, [1, 1])
        with self.assertRaises(TypeError):
            allocate(10, [1, True])


if __name__ == "__main__":
    unittest.main()
