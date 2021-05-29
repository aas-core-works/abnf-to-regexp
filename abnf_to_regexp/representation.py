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
        hexord = format(ord(symbol), "x")
        return f"\\x{hexord}"
    elif ord(symbol) > 255:
        hexord = format(ord(symbol), "x")
        return f"\\u{hexord}"
    else:
        return symbol
