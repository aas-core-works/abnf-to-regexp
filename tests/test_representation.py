# pylint: disable=missing-docstring

import unittest

from abnf_to_regexp.representation import escape_for_character_class, escape_literal


# noinspection PyPep8Naming
class Test_escape_for_character_class(
    unittest.TestCase
):  # pylint: disable=invalid-name
    def test_empty_string(self) -> None:
        self.assertEqual("", escape_for_character_class(""))

    def test_dash_character(self) -> None:
        self.assertEqual("\\-", escape_for_character_class("-"))

    def test_backslash_character(self) -> None:
        self.assertEqual("\\\\", escape_for_character_class("\\"))

    def test_left_bracket(self) -> None:
        self.assertEqual("\\[", escape_for_character_class("["))

    def test_right_bracket(self) -> None:
        self.assertEqual("\\]", escape_for_character_class("]"))

    def test_regular_ascii_characters(self) -> None:
        self.assertEqual("a", escape_for_character_class("a"))
        self.assertEqual("Z", escape_for_character_class("Z"))
        self.assertEqual("5", escape_for_character_class("5"))
        self.assertEqual("_", escape_for_character_class("_"))
        self.assertEqual("@", escape_for_character_class("@"))

    def test_hash_sign(self) -> None:
        self.assertEqual("#", escape_for_character_class("#"))

    def test_non_printable_ascii(self) -> None:
        self.assertEqual("\\x00", escape_for_character_class("\x00"))
        self.assertEqual("\\x01", escape_for_character_class("\x01"))
        self.assertEqual("\\x1f", escape_for_character_class("\x1f"))
        self.assertEqual("\\x7f", escape_for_character_class("\x7f"))
        self.assertEqual("\\xff", escape_for_character_class("\xff"))

    def test_unicode_in_bmp(self) -> None:
        self.assertEqual("\\xa0", escape_for_character_class("\u00a0"))
        self.assertEqual("\\u03b1", escape_for_character_class("α"))
        self.assertEqual("\\u4e2d", escape_for_character_class("中"))
        self.assertEqual("\\uffff", escape_for_character_class("\uffff"))

    def test_unicode_above_bmp(self) -> None:
        self.assertEqual("\\U00010000", escape_for_character_class("\U00010000"))
        self.assertEqual("\\U0001f600", escape_for_character_class("😀"))
        self.assertEqual("\\U0002f800", escape_for_character_class("\U0002f800"))
        self.assertEqual("\\U0010ffff", escape_for_character_class("\U0010ffff"))

    def test_printable_special_characters(self) -> None:
        self.assertEqual("!", escape_for_character_class("!"))
        self.assertEqual("$", escape_for_character_class("$"))
        self.assertEqual("%", escape_for_character_class("%"))
        self.assertEqual("&", escape_for_character_class("&"))
        self.assertEqual("(", escape_for_character_class("("))
        self.assertEqual(")", escape_for_character_class(")"))
        self.assertEqual("*", escape_for_character_class("*"))
        self.assertEqual("+", escape_for_character_class("+"))
        self.assertEqual(".", escape_for_character_class("."))
        self.assertEqual("?", escape_for_character_class("?"))
        self.assertEqual("^", escape_for_character_class("^"))
        self.assertEqual("|", escape_for_character_class("|"))


# noinspection PyPep8Naming
class Test_escape_literal(unittest.TestCase):  # pylint: disable=invalid-name
    def test_empty_string(self) -> None:
        self.assertEqual("", escape_literal(""))

    def test_simple_alphanumeric(self) -> None:
        self.assertEqual("hello", escape_literal("hello"))
        self.assertEqual("Hello123", escape_literal("Hello123"))
        self.assertEqual("test_var", escape_literal("test_var"))
        self.assertEqual("a-b", escape_literal("a-b"))
        self.assertEqual("ABC-123_xyz", escape_literal("ABC-123_xyz"))

    def test_hash_sign_not_escaped(self) -> None:
        self.assertEqual("#", escape_literal("#"))
        self.assertEqual("a#b", escape_literal("a#b"))

    def test_slash_not_escaped(self) -> None:
        # NOTE (mristin):
        # We explicitly check that we do not escape the slash as it is only used in
        # JavaScript regex engine.
        self.assertEqual("/", escape_literal("/"))

    def test_regex_special_characters_escaped(self) -> None:
        self.assertEqual("\\.", escape_literal("."))
        self.assertEqual("\\*", escape_literal("*"))
        self.assertEqual("\\+", escape_literal("+"))
        self.assertEqual("\\?", escape_literal("?"))
        self.assertEqual("\\^", escape_literal("^"))
        self.assertEqual("\\$", escape_literal("$"))
        self.assertEqual("\\|", escape_literal("|"))
        self.assertEqual("\\(", escape_literal("("))
        self.assertEqual("\\)", escape_literal(")"))
        self.assertEqual("\\[", escape_literal("["))
        self.assertEqual("\\]", escape_literal("]"))
        self.assertEqual("\\{", escape_literal("{"))
        self.assertEqual("\\}", escape_literal("}"))
        self.assertEqual("\\\\", escape_literal("\\"))

    def test_mixed_content(self) -> None:
        self.assertEqual("hello\\.world", escape_literal("hello.world"))
        self.assertEqual("test\\*pattern", escape_literal("test*pattern"))
        self.assertEqual("a\\+b-c", escape_literal("a+b-c"))

    def test_non_printable_ascii(self) -> None:
        self.assertEqual("\\x00", escape_literal("\x00"))
        self.assertEqual("\\x01", escape_literal("\x01"))
        self.assertEqual("\\x1f", escape_literal("\x1f"))
        self.assertEqual("\\x7f", escape_literal("\x7f"))
        self.assertEqual("\\xff", escape_literal("\xff"))

    def test_unicode_in_bmp(self) -> None:
        self.assertEqual("\\xa0", escape_literal("\u00a0"))
        self.assertEqual("\\u03b1", escape_literal("α"))
        self.assertEqual("\\u4e2d", escape_literal("中"))
        self.assertEqual("\\uffff", escape_literal("\uffff"))

    def test_unicode_above_bmp(self) -> None:
        self.assertEqual("\\U00010000", escape_literal("\U00010000"))
        self.assertEqual("\\U0001f600", escape_literal("😀"))
        self.assertEqual("\\U0002f800", escape_literal("\U0002f800"))
        self.assertEqual("\\U0010ffff", escape_literal("\U0010ffff"))

    def test_complex_mixed_string(self) -> None:
        input_str = "hello.world*test#中文😀\x01"
        expected = "hello\\.world\\*test#\\u4e2d\\u6587\\U0001f600\\x01"
        self.assertEqual(expected, escape_literal(input_str))

    def test_whitespace_characters(self) -> None:
        self.assertEqual(" ", escape_literal(" "))
        self.assertEqual("\\t", escape_literal("\t"))
        self.assertEqual("\\n", escape_literal("\n"))
        self.assertEqual("\\r", escape_literal("\r"))

    def test_boundary_unicode_values(self) -> None:
        self.assertEqual("\\xff", escape_literal("\u00ff"))
        self.assertEqual("\\u0100", escape_literal("\u0100"))
        self.assertEqual("\\uffff", escape_literal("\uffff"))
        self.assertEqual("\\U00010000", escape_literal("\U00010000"))


if __name__ == "__main__":
    unittest.main()
