import unittest

from solution import install_order


class TestInstallOrderRules(unittest.TestCase):
    def test_alphabetical_among_ready(self):
        self.assertEqual(install_order({"c": [], "a": [], "b": []}), ["a", "b", "c"])
        self.assertEqual(install_order({"z": [], "a": ["z"], "m": []}), ["m", "z", "a"])

    def test_ready_order_is_decided_at_each_step(self):
        packages = {"a": ["d"], "b": [], "c": ["b"], "d": []}
        self.assertEqual(install_order(packages), ["b", "c", "d", "a"])

    def test_diamond(self):
        packages = {"top": ["left", "right"], "left": ["base"], "right": ["base"], "base": []}
        self.assertEqual(install_order(packages), ["base", "left", "right", "top"])

    def test_duplicate_dependencies(self):
        self.assertEqual(install_order({"a": ["b", "b"], "b": []}), ["b", "a"])

    def test_empty(self):
        self.assertEqual(install_order({}), [])

    def test_missing_dependency(self):
        with self.assertRaises(KeyError):
            install_order({"a": ["ghost"]})

    def test_self_dependency(self):
        with self.assertRaises(ValueError) as caught:
            install_order({"a": ["a"]})
        self.assertEqual(str(caught.exception), "a -> a")

    def test_cycle_message(self):
        with self.assertRaises(ValueError) as caught:
            install_order({"c": ["a"], "a": ["b"], "b": ["c"]})
        self.assertEqual(str(caught.exception), "a -> b -> c -> a")

    def test_cycle_message_starts_at_smallest_name(self):
        with self.assertRaises(ValueError) as caught:
            install_order({"x": ["m"], "m": ["x"], "free": []})
        self.assertEqual(str(caught.exception), "m -> x -> m")

    def test_cycle_with_tail(self):
        packages = {"app": ["b"], "b": ["c"], "c": ["b"], "ok": []}
        with self.assertRaises(ValueError) as caught:
            install_order(packages)
        self.assertEqual(str(caught.exception), "b -> c -> b")

    def test_input_is_not_modified(self):
        packages = {"a": ["b", "b"], "b": []}
        install_order(packages)
        self.assertEqual(packages, {"a": ["b", "b"], "b": []})


if __name__ == "__main__":
    unittest.main()
