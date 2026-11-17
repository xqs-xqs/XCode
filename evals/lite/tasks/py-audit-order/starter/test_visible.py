import unittest

from solution import install_order


class TestInstallOrder(unittest.TestCase):
    def test_chain(self):
        self.assertEqual(install_order({"app": ["lib"], "lib": ["core"], "core": []}), ["core", "lib", "app"])

    def test_no_dependencies(self):
        self.assertEqual(install_order({"only": []}), ["only"])

    def test_reported_alphabetical_order(self):
        self.assertEqual(install_order({"c": [], "a": [], "b": []}), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
