import unittest

from solution import render


class TestRender(unittest.TestCase):
    def test_placeholder(self):
        self.assertEqual(render("Hello {name}!", {"name": "Ada"}), "Hello Ada!")

    def test_filter(self):
        self.assertEqual(render("{name|upper}", {"name": "Ada"}), "ADA")

    def test_plain_text(self):
        self.assertEqual(render("no placeholders", {}), "no placeholders")


if __name__ == "__main__":
    unittest.main()
