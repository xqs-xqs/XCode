import unittest

from solution import satisfies


class TestSatisfiesRules(unittest.TestCase):
    def test_equal_forms(self):
        self.assertTrue(satisfies("1.2.3", "=1.2.3"))
        self.assertFalse(satisfies("1.2.3", "=1.2.4"))

    def test_comparators_compare_numerically(self):
        self.assertTrue(satisfies("1.10.0", ">1.9.0"))
        self.assertFalse(satisfies("1.9.0", ">1.10.0"))
        self.assertTrue(satisfies("1.2.3", "<=1.2.3"))
        self.assertFalse(satisfies("1.2.3", "<1.2.3"))
        self.assertFalse(satisfies("1.2.3", ">1.2.3"))

    def test_caret_major(self):
        self.assertTrue(satisfies("1.2.3", "^1.2.3"))
        self.assertFalse(satisfies("1.2.2", "^1.2.3"))
        self.assertFalse(satisfies("2.0.0", "^1.2.3"))

    def test_caret_zero_major(self):
        self.assertTrue(satisfies("0.2.9", "^0.2.3"))
        self.assertFalse(satisfies("0.3.0", "^0.2.3"))
        self.assertTrue(satisfies("0.0.3", "^0.0.3"))
        self.assertFalse(satisfies("0.0.4", "^0.0.3"))
        self.assertTrue(satisfies("0.0.0", "^0.0.0"))
        self.assertFalse(satisfies("0.0.1", "^0.0.0"))

    def test_tilde(self):
        self.assertTrue(satisfies("1.2.9", "~1.2.3"))
        self.assertFalse(satisfies("1.3.0", "~1.2.3"))
        self.assertFalse(satisfies("1.2.2", "~1.2.3"))

    def test_partial_versions_are_padded(self):
        self.assertTrue(satisfies("1.2.0", ">=1.2"))
        self.assertTrue(satisfies("1.0.0", "1"))
        self.assertFalse(satisfies("1.0.1", "1"))
        self.assertTrue(satisfies("1.9.0", "^1"))
        self.assertFalse(satisfies("2.0.0", "^1"))
        self.assertTrue(satisfies("1.0.5", "~1"))
        self.assertFalse(satisfies("1.1.0", "~1"))
        self.assertFalse(satisfies("0.0.1", "^0"))

    def test_star(self):
        self.assertTrue(satisfies("0.0.0", "*"))
        self.assertTrue(satisfies("9.9.9", "* >=1.0.0"))
        self.assertFalse(satisfies("0.9.9", "* >=1.0.0"))

    def test_alternatives(self):
        self.assertTrue(satisfies("3.1.0", "^1.0.0 || ^3.0.0"))
        self.assertFalse(satisfies("2.1.0", "^1.0.0 || ^3.0.0"))
        self.assertTrue(satisfies("1.0.0", "1.0.0||2.0.0"))

    def test_malformed_version(self):
        for version in ("1.2", "1.2.3.4", "01.2.3", "1.2.x", "", "v1.2.3", "1.2.3 "):
            with self.assertRaises(ValueError, msg=version):
                satisfies(version, "*")

    def test_malformed_spec(self):
        for spec in ("", "   ", "1.2.3 ||", "|| 1.2.3", ">= 1.2.3", "=>1.2.3", "!1.2.3", "^01.0.0", "1.2.3.4", "^", "~x"):
            with self.assertRaises(ValueError, msg=spec):
                satisfies("1.2.3", spec)

    def test_malformed_spec_raises_even_after_a_match(self):
        with self.assertRaises(ValueError):
            satisfies("1.2.3", "1.2.3 || bogus")


if __name__ == "__main__":
    unittest.main()
