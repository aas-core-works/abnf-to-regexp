"""List all the letter ranges as ranges of unicode characters."""

import sys

import regex

_ORD_LOWER_A = ord("a")
_ORD_LOWER_Z = ord("z")
_ORD_UPPER_A = ord("A")
_ORD_UPPER_Z = ord("Z")


def repr_character_ord(ordinal: int) -> str:
    """Represent the character ordinal as a Python string literal."""
    if ordinal <= 255:
        if (
            _ORD_LOWER_A <= ordinal <= _ORD_LOWER_Z
            or _ORD_UPPER_A <= ordinal <= _ORD_UPPER_Z
        ):
            return repr(chr(ordinal))
        else:
            return f"'\\x{ordinal:02x}'"
    elif ordinal <= 2**16 - 1:
        return f"'\\u{ordinal:04x}'"
    else:
        return f"'\\U{ordinal:08x}'"


def main() -> int:
    """Execute the main routine."""
    letter_re = regex.compile(r"\p{L}")
    start = None

    assert letter_re.match("a")

    for i in range(0x110000):
        character = chr(i)

        if letter_re.match(character):
            if start is None:
                start = repr_character_ord(ordinal=i)

        else:
            if start is not None:
                end = repr_character_ord(ordinal=i - 1)
                print(f"({start}, {end}),")
                start = None

    return 0


if __name__ == "__main__":
    sys.exit(main())
