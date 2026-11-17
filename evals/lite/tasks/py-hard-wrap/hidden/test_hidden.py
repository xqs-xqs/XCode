import unittest

from solution import wrap


class TestWrapRules(unittest.TestCase):
    def test_exact_fit(self):
        self.assertEqual(wrap("a b c", 3), ["a b", "c"])
        self.assertEqual(wrap("hello world", 11), ["hello world"])
        self.assertEqual(wrap("hello world", 10), ["hello", "world"])

    def test_whitespace_only_separates_words(self):
        self.assertEqual(wrap("  a \t b\nc  ", 10), ["a b c"])

    def test_long_word_is_cut(self):
        self.assertEqual(wrap("abcdefgh", 3), ["abc", "def", "gh"])
        self.assertEqual(wrap("abcdef", 3), ["abc", "def"])

    def test_long_word_starts_new_line(self):
        self.assertEqual(wrap("x abcdefgh y", 3), ["x", "abc", "def", "gh", "y"])

    def test_next_word_may_join_last_chunk(self):
        self.assertEqual(wrap("x abcdef y", 4), ["x", "abcd", "ef y"])
        self.assertEqual(wrap("abcdef yz", 4), ["abcd", "ef", "yz"])

    def test_paragraphs(self):
        self.assertEqual(wrap("a\n\nb", 5), ["a", "", "b"])
        self.assertEqual(wrap("a b\n \t \n\n\nc d", 3), ["a b", "", "c d"])

    def test_no_empty_string_at_the_edges(self):
        self.assertEqual(wrap("\n\na\n\n", 5), ["a"])
        self.assertEqual(wrap("\n \n a b \n\n c \n \n", 5), ["a b", "", "c"])

    def test_no_words(self):
        self.assertEqual(wrap("", 5), [])
        self.assertEqual(wrap("  \n \t\n", 5), [])

    def test_width_one(self):
        self.assertEqual(wrap("ab c", 1), ["a", "b", "c"])

    def test_no_edge_spaces(self):
        for line in wrap("one  two   three four five six seven", 9):
            self.assertEqual(line, line.strip())
            self.assertLessEqual(len(line), 9)

    def test_invalid_width(self):
        for width in (0, -1):
            with self.assertRaises(ValueError):
                wrap("a", width)


if __name__ == "__main__":
    unittest.main()
