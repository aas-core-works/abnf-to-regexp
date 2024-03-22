"""Provide common functions for representing regular expressions."""

import string


def escape_for_character_class(symbol: str) -> str:
    """Escape the symbol which needs to appear in a character class."""
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
