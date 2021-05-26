"""Convert ABNF grammars to Python regular expressions."""

import abc
import argparse
import pathlib
import string
import sys
from typing import Optional, TextIO, Union, Type, List, Iterable

import abnf
import regex as re
from icontract import require

import abnf_to_regexp

assert __doc__ == abnf_to_regexp.__doc__

Parser = Union[
    abnf.Rule,
    abnf.parser.Literal,
    abnf.parser.Concatenation,
    abnf.parser.Option,
    abnf.parser.Alternation,
    abnf.parser.Repetition,
]


class Element(abc.ABC):
    """Represent a general regular expression element."""


class Concatenation(Element):
    """Represent a concatenation of regular expression elements."""

    def __init__(self, elements: Iterable[Element]) -> None:
        """Initialize with the given values."""
        self.elements = elements


class Alternation(Element):
    """Represent an alteration of regular expression elements."""

    def __init__(self, elements: Iterable[Element]) -> None:
        """Initialize with the given values."""
        self.elements = elements


class Repetition(Element):
    """Represent a repetition group."""

    def __init__(
        self,
        element: Element,
        min_occurrences: Optional[int],
        max_occurrences: Optional[int],
    ) -> None:
        """Initialize with the given values."""
        self.element = element
        self.min_occurrences = min_occurrences
        self.max_occurrences = max_occurrences


class CaseInsensitivity(Element):
    """Represent a part of the regular expression for which case insensitivity holds."""

    def __init__(self, element: Element) -> None:
        """Initialize with the given values."""
        self.element = element


class Literal(Element):
    """Represent a literal match in the regular expression."""

    def __init__(self, value: str) -> None:
        """Initialize with the given values."""
        self.value = value


class Range(Element):
    """Represent a range match in the regular expression."""

    @require(lambda start: len(start) == 1)
    @require(lambda end: len(end) == 1)
    def __init__(self, start: str, end: str) -> None:
        """Initialize with the given values."""
        self.start = start
        self.end = end


class CharacterClass(Element):
    """Represent a list of ranges which all apply."""

    # fmt: off
    @require(
        lambda elements:
        all(
            len(element.value) == 1
            for element in elements
            if isinstance(element, Literal))
    )
    # fmt: on
    def __init__(self, elements: Iterable[Union[Range, Literal]]) -> None:
        """Initialize with the given values."""
        self.elements = elements


def _translate_parser(parser: Parser) -> Element:
    """Translate a parser to a regular expression."""
    if isinstance(parser, abnf.Rule):
        return _translate_rule(rule=parser)

    elif isinstance(parser, abnf.parser.Literal):
        return _translate_literal(literal=parser)

    elif isinstance(parser, abnf.parser.Concatenation):
        return _translate_concatenation(parsers=parser.parsers)

    elif isinstance(parser, abnf.parser.Option):
        return _translate_option(option=parser)

    elif isinstance(parser, abnf.parser.Alternation):
        return _translate_alteration(parsers=parser.parsers)

    elif isinstance(parser, abnf.parser.Repetition):
        return _translate_repetition(repeat=parser.repeat, element=parser.element)

    else:
        raise NotImplementedError(str(parser))


def _translate_option(option: abnf.parser.Option) -> Element:
    """Translate an option to a regular expression."""
    return Repetition(
        element=_translate_parser(parser=option.alternation),
        min_occurrences=0,
        max_occurrences=1,
    )


def _translate_alteration(parsers: Iterable[Parser]) -> Element:
    """Translate an alteration to a regular expression."""
    return Alternation(
        elements=[_translate_parser(parser=parser) for parser in parsers]
    )


def _translate_repetition(repeat: abnf.parser.Repeat, element: Parser) -> Element:
    """Translate a repetition to a regular expression."""
    return Repetition(
        element=_translate_parser(parser=element),
        min_occurrences=repeat.min,
        max_occurrences=repeat.max,
    )


def _translate_concatenation(parsers: Iterable[Parser]) -> Element:
    """Translate a concatenation to a regular expression."""
    return Concatenation(elements=[_translate_parser(parser) for parser in parsers])


def _translate_literal(literal: abnf.parser.Literal) -> Element:
    """Translate an ABNF literal to a regular expression."""
    if isinstance(literal.pattern, tuple):
        assert len(literal.pattern) == 2, (
            f"Expected literal pattern to have only two elements, start and end, "
            f"but got: {literal.pattern}"
        )

        start, end = literal.pattern

        result = Range(start=start, end=end)  # type: Element

        if (
            not literal.case_sensitive
            and re.search(r"\p{L}", start)
            and re.search(r"\p{L}", end)
        ):
            result = CaseInsensitivity(element=result)

        return result

    else:
        assert isinstance(literal.pattern, str)
        result = Literal(value=literal.value)

        if not literal.case_sensitive and re.search(r"\p{L}", literal.value):
            result = CaseInsensitivity(element=result)

        return result


def _translate_rule(rule: abnf.Rule) -> Element:
    """Translate the ABNF element to a regular expression."""
    if rule.name == "ALPHA":
        return CharacterClass(
            elements=[Range(start="a", end="z"), Range(start="A", end="Z")]
        )
    elif rule.name == "DIGIT":
        return Range(start="0", end="9")
    elif rule.name == "HEXDIG":
        return CharacterClass(
            elements=[
                Range(start="0", end="9"),
                Range(start="A", end="F"),
                Range(start="a", end="f"),
            ]
        )
    elif rule.name == "BIT":
        return CharacterClass(elements=[Literal(value="0"), Literal(value="1")])
    elif rule.name == "DQUOTE":
        return Literal(value='"')
    if isinstance(rule.definition, abnf.parser.Concatenation):
        return _translate_concatenation(parsers=rule.definition.parsers)
    elif isinstance(rule.definition, abnf.parser.Alternation):
        return _translate_alteration(parsers=rule.definition.parsers)
    elif isinstance(rule.definition, abnf.parser.Repetition):
        return _translate_repetition(
            repeat=rule.definition.repeat, element=rule.definition.element
        )
    elif isinstance(rule.definition, abnf.parser.Literal):
        return _translate_literal(literal=rule.definition)
    else:
        raise AssertionError(f"Unhandled rule definition: {rule.definition}")


@require(lambda rule_cls: len(rule_cls.rules()) > 0)
def translate(rule_cls: Type[abnf.Rule]) -> Element:
    """Translate the ABNF rule to a regular expression."""
    return _translate_rule(rule=rule_cls.rules()[0])


class _Transformer:
    """Transform recursively a regular expression."""

    # pylint: disable=missing-docstring,no-self-use

    def transform(self, element: Element) -> Element:
        if isinstance(element, Concatenation):
            return self.transform_concatenation(element)
        elif isinstance(element, Alternation):
            return self.transform_alternation(element)
        elif isinstance(element, Repetition):
            return self.transform_repetition(element)
        elif isinstance(element, CaseInsensitivity):
            return self.transform_case_insensitivity(element)
        elif isinstance(element, Literal):
            return self.transform_literal(element)
        elif isinstance(element, Range):
            return self.transform_range(element)
        elif isinstance(element, CharacterClass):
            return self.transform_character_class(element)
        else:
            return self.transform_default(element)

    def transform_concatenation(self, element: Concatenation) -> Element:
        return Concatenation(
            elements=[self.transform(subelement) for subelement in element.elements]
        )

    def transform_alternation(self, element: Alternation) -> Element:
        return Alternation(
            elements=[self.transform(subelement) for subelement in element.elements]
        )

    def transform_repetition(self, element: Repetition) -> Element:
        return Repetition(
            element=self.transform(element.element),
            min_occurrences=element.min_occurrences,
            max_occurrences=element.max_occurrences,
        )

    def transform_case_insensitivity(self, element: CaseInsensitivity) -> Element:
        return CaseInsensitivity(element=self.transform(element.element))

    def transform_literal(self, element: Literal) -> Element:
        return element

    def transform_range(self, element: Range) -> Element:
        return element

    def transform_character_class(self, element: CharacterClass) -> Element:
        return element

    def transform_default(self, element: Element) -> Element:
        raise AssertionError(f"Unhandled transformation of an element: {element}")


class _MergeAlternations(_Transformer):
    def transform_alternation(self, element: Alternation) -> Element:
        transformed_subelements = [
            self.transform(subelement) for subelement in element.elements
        ]

        if all(isinstance(subel, Alternation) for subel in transformed_subelements):
            merged = []  # type: List[Element]
            for subel in transformed_subelements:
                assert isinstance(subel, Alternation)
                merged.extend(subel.elements)

            return Alternation(elements=merged)

        return element


def merge_alternations(element: Element) -> Element:
    """Merge all alternations of alternations."""
    return _MergeAlternations().transform(element)


class _MergeAlternationsOfCharacterClasses(_Transformer):
    def transform_alternation(self, element: Alternation) -> Element:
        transformed_subelements = [
            self.transform(subelement) for subelement in element.elements
        ]

        can_merge = True
        for subel in transformed_subelements:
            if not isinstance(subel, (Literal, Range, CharacterClass)):
                can_merge = False
                break

            if isinstance(subel, Literal) and len(subel.value) > 1:
                can_merge = False
                break

        if not can_merge:
            return Alternation(elements=transformed_subelements)

        merged = []  # type: List[Union[Range, Literal]]
        for subel in transformed_subelements:
            if isinstance(subel, CharacterClass):
                merged.extend(subel.elements)
            elif isinstance(subel, Literal):
                merged.append(subel)
            elif isinstance(subel, Range):
                merged.append(subel)
            else:
                raise AssertionError(str(subel))

        return CharacterClass(elements=merged)


def merge_alternations_of_character_classes(element: Element) -> Element:
    """Merge alternations of character classes into a single character class."""
    return _MergeAlternationsOfCharacterClasses().transform(element)


def _escape_for_range(symbol: str) -> str:
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


def represent(element: Element) -> str:
    """Represent the regular expression as a string pattern."""
    if isinstance(element, Concatenation):
        return "".join(represent(part) for part in element.elements)
    elif isinstance(element, Alternation):
        return "".join(
            ("(", "|".join(represent(part) for part in element.elements), ")")
        )
    elif isinstance(element, Repetition):
        if element.min_occurrences == 0 and element.max_occurrences is None:
            return f"({represent(element.element)})*"
        elif element.min_occurrences == 0 and element.max_occurrences == 1:
            return f"({represent(element.element)})?"
        elif (
            (element.min_occurrences is None or element.min_occurrences == 0)
            and element.max_occurrences is not None
            and element.max_occurrences > 0
        ):
            return f"({represent(element.element)}){{{element.max_occurrences}}}"
        elif (
            element.min_occurrences is not None
            and element.min_occurrences > 0
            and element.max_occurrences is None
        ):
            return f"({represent(element.element)}){{{element.min_occurrences},}}"
        else:
            return (
                f"({represent(element.element)})"
                + f"{{{element.min_occurrences},{element.max_occurrences}}}"
            )
    elif isinstance(element, CaseInsensitivity):
        return f"(?i:{represent(element.element)})"
    elif isinstance(element, Literal):
        escaped_value = re.escape(element.value)
        assert isinstance(escaped_value, str)
        return escaped_value
    elif isinstance(element, Range):
        return "".join(
            (
                "[",
                _escape_for_range(element.start),
                "-",
                _escape_for_range(element.end),
                "]",
            )
        )
    elif isinstance(element, CharacterClass):
        parts = []  # type: List[str]
        for subelement in element.elements:
            if isinstance(subelement, Range):
                parts.extend(
                    (
                        _escape_for_range(subelement.start),
                        "-",
                        _escape_for_range(subelement.end),
                    )
                )
            elif isinstance(subelement, Literal):
                parts.append(_escape_for_range(subelement.value))
            else:
                raise NotImplementedError(
                    f"sub-element {subelement} in element {element}"
                )

        return "".join(["["] + parts + ["]"])
    else:
        raise AssertionError(f"Unhandled element: {element}")


def run(
    input_path: pathlib.Path,
    output_path: Optional[pathlib.Path],
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Execute the main routine."""
    pass  # for pydocstyle

    class Rule(abnf.Rule):  # type: ignore
        """Represent our ABNF rule list read from a file."""

        pass

    try:
        Rule.from_file(input_path)
    except abnf.ParseError as err:
        text = input_path.read_text()
        line = 1
        for i, symbol in enumerate(text):
            if i == err.start:
                break

            if symbol == "\n":
                line += 1

        stderr.write(
            f"Parsing error at line {line}: {err}:\n\n"
            f"{text[err.start:err.start + 200]!r};\n"
            "did you make sure that the line endings are stored as CRLF?"
        )
        return 1

    except abnf.GrammarError as err:
        stderr.write(f"Failed to interpret the grammar: {err}")
        return 1

    regexp = translate(rule_cls=Rule)
    regexp = merge_alternations(regexp)
    regexp = merge_alternations_of_character_classes(regexp)

    representation = represent(regexp)

    representation_nl = representation + "\n"
    if output_path is None:
        stdout.write(representation_nl)
    else:
        output_path.write_text(representation_nl, encoding="utf-8")

    return 0


def main() -> int:
    """Wrap the main routine."""
    parser = argparse.ArgumentParser(prog="abnf-to-regexp", description=__doc__)
    parser.add_argument("-i", "--input", help="path to the ABNF file", required=True)
    parser.add_argument(
        "-o",
        "--output",
        help="path to the file where regular expression is stored; "
        "if not specified, writes to STDOUT",
    )
    args = parser.parse_args()

    input_pth = pathlib.Path(args.input)
    output_pth = pathlib.Path(args.output) if args.output else None

    return run(
        input_path=input_pth,
        output_path=output_pth,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    sys.exit(main())
