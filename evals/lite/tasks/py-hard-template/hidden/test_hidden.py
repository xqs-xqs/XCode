import unittest

from solution import render


class TestRenderRules(unittest.TestCase):
    def test_non_string_values(self):
        self.assertEqual(render("{n} items, {flag}, {x}", {"n": 3, "flag": True, "x": None}), "3 items, True, None")

    def test_dotted_names(self):
        values = {"user": {"name": "Ada", "address": {"city": "Paris"}}}
        self.assertEqual(render("{user.name} in {user.address.city}", values), "Ada in Paris")

    def test_escaped_braces(self):
        self.assertEqual(render("{{}}", {}), "{}")
        self.assertEqual(render("{{name}}", {"name": "x"}), "{name}")
        self.assertEqual(render("{{{name}}}", {"name": "x"}), "{x}")
        self.assertEqual(render("a }} b {{ c", {}), "a } b { c")

    def test_filters_chain_left_to_right(self):
        self.assertEqual(render("{v|trim|upper}", {"v": "  ab "}), "AB")
        self.assertEqual(render("{v|upper|lower}", {"v": "Ab"}), "ab")
        self.assertEqual(render("{v|title}", {"v": "hello world"}), "Hello World")
        self.assertEqual(render("[{v|trim}]", {"v": " x "}), "[x]")

    def test_whitespace_inside_placeholder(self):
        self.assertEqual(render("{ name | upper }", {"name": "ada"}), "ADA")
        self.assertEqual(render("{ user.name }", {"user": {"name": "ada"}}), "ada")

    def test_filter_applies_to_string_form(self):
        self.assertEqual(render("{n|upper}", {"n": 12}), "12")
        self.assertEqual(render("{flag|lower}", {"flag": True}), "true")

    def test_missing_names(self):
        with self.assertRaises(KeyError):
            render("{missing}", {})
        with self.assertRaises(KeyError):
            render("{user.age}", {"user": {"name": "x"}})
        with self.assertRaises(KeyError):
            render("{user.name.first}", {"user": {"name": "x"}})

    def test_unknown_or_empty_filter(self):
        for template in ("{name|shout}", "{name|}", "{name||upper}", "{name|upper|}"):
            with self.assertRaises(ValueError, msg=template):
                render(template, {"name": "x"})

    def test_malformed_placeholders(self):
        for template in ("{}", "{ }", "{a-b}", "{a..b}", "{.a}", "{a.}", "{|upper}", "{a b}"):
            with self.assertRaises(ValueError, msg=template):
                render(template, {"a": {"b": "x"}, "a-b": "x", "a b": "x"})

    def test_unbalanced_braces(self):
        for template in ("{name", "name}", "{name}}", "a { b", "}"):
            with self.assertRaises(ValueError, msg=template):
                render(template, {"name": "x"})

    def test_text_is_copied_unchanged(self):
        self.assertEqual(render("  a|b . c\n", {}), "  a|b . c\n")


if __name__ == "__main__":
    unittest.main()
