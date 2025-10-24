"""Provide common functions for representing regular expressions."""

import io
import re
import string
from typing import List, Tuple


def escape_for_character_class(symbol: str) -> str:
    """Escape the symbol which needs to appear in a character class."""
    if len(symbol) == 0:
        return ""

    if symbol == "-":
        return "\\-"
    elif symbol == "\\":
        return "\\\\"
    elif symbol == "[":
        return "\\["
    elif symbol == "]":
        return "\\]"
    elif symbol not in string.printable and ord(symbol) <= 255:
        return f"\\x{ord(symbol):02x}"
    elif 255 < ord(symbol) < 0x00010000:
        return f"\\u{ord(symbol):04x}"
    elif 0x10000 <= ord(symbol) <= 0x10FFFF:
        return f"\\U{ord(symbol):08x}"
    else:
        return symbol


# The hash sign (``#``) only has a special meaning when in re.VERBOSE
# mode. So it is okay to leave it un-escaped. This helps to be more
# compatible with other regular expression engines, as for Javascript's
# unicode-aware RegExp the number sign must not be quoted.

_NO_NEED_TO_ESCAPE_IN_LITERAL_RE = re.compile(r"[a-zA-Z_0-9\- #:,;=@~`'\"!%&<>/]*")


def _generate_no_need_to_escape_tuple() -> Tuple[bool, ...]:
    lst: List[bool] = []
    for i in range(256):
        char = chr(i)

        lst.append(_NO_NEED_TO_ESCAPE_IN_LITERAL_RE.fullmatch(char) is not None)

    return tuple(lst)


_NO_NEED_TO_ESCAPE_IN_LITERAL_TUPLE = _generate_no_need_to_escape_tuple()


def _generate_escaping_tuple() -> Tuple[str, ...]:
    escaping_at: List[str] = []

    for i in range(256):
        char = chr(i)

        if _NO_NEED_TO_ESCAPE_IN_LITERAL_RE.fullmatch(char) is not None:
            escaped = char

        # Friendly control chars
        elif char == "\\0":
            escaped = r"\0"
        elif char == "\a":
            escaped = r"\a"
        elif char == "\b":
            escaped = r"\b"
        elif char == "\t":
            escaped = r"\t"
        elif char == "\n":
            escaped = r"\n"
        elif char == "\v":
            escaped = r"\v"
        elif char == "\f":
            escaped = r"\f"
        elif char == "\r":
            escaped = r"\r"

        # Single-character escapes for regex meta-characters
        elif char == "\\":
            escaped = r"\\"
        elif char == ".":
            escaped = r"\."
        elif char == "^":
            escaped = r"\^"
        elif char == "$":
            escaped = r"\$"
        elif char == "*":
            escaped = r"\*"
        elif char == "+":
            escaped = r"\+"
        elif char == "?":
            escaped = r"\?"
        elif char == "(":
            escaped = r"\("
        elif char == ")":
            escaped = r"\)"
        elif char == "[":
            escaped = r"\["
        elif char == "]":
            escaped = r"\]"
        elif char == "{":
            escaped = r"\{"
        elif char == "}":
            escaped = r"\}"
        elif char == "|":
            escaped = r"\|"
        else:
            escaped = f"\\x{i:02x}"

        escaping_at.append(escaped)

    return tuple(escaping_at)


_ESCAPING_TUPLE = _generate_escaping_tuple()


def escape_literal(text: str) -> str:
    """
    Escape the individual characters of a literal.

    ``re.escape`` is a bit too conservative and produces unreadable regular expressions.
    To make the expressions more readable, we avoid escaping the cases where we are sure
    no escapes are necessary.
    """
    if len(text) == 0:
        return ""

    # NOTE (mristin):
    # We use `all` + whitelisting to avoid the slow regex fullmatch which always create
    # a match object.
    if all(
        ord(character) <= 255 and _NO_NEED_TO_ESCAPE_IN_LITERAL_TUPLE[ord(character)]
        for character in text
    ):
        return text
    else:
        stream = io.StringIO()

        for character in text:
            ord_character = ord(character)

            if ord_character <= 255:
                escaped_value = _ESCAPING_TUPLE[ord_character]
            elif 255 < ord_character < 0x10000:
                escaped_value = f"\\u{ord_character:04x}"
            elif 0x10000 <= ord_character <= 0x10FFFF:
                escaped_value = f"\\U{ord_character:08x}"
            else:
                escaped_value = re.escape(character)

            assert isinstance(escaped_value, str)
            stream.write(escaped_value)

        return stream.getvalue()
