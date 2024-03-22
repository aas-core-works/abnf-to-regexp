"""Transform ABNF to a single regular expression."""

from typing import Type, List

import abnf
import regex as re
from icontract import require

import abnf_to_regexp.abnf_transformation
import abnf_to_regexp.compression
from abnf_to_regexp.base import (
    Element,
    Repetition,
    Alternation,
    Concatenation,
    Range,
    CaseInsensitivity,
    Literal,
    CharacterClass,
    Convertor,
    Reference,
)
from abnf_to_regexp.representation import escape_for_character_class


class ABNFTransformer(abnf_to_regexp.abnf_transformation.TransformerToElement):
    """Translate ABNF rule set to a single regular expression."""

    def transform_rule(self, rule: abnf.Rule) -> Element:
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
            return self.transform_concatenation(parsers=rule.definition.parsers)
        elif isinstance(rule.definition, abnf.parser.Alternation):
            return self.transform_alternation(parsers=rule.definition.parsers)
        elif isinstance(rule.definition, abnf.parser.Repetition):
            return self.transform_repetition(
                repeat=rule.definition.repeat, parser=rule.definition.element
            )
        elif isinstance(rule.definition, abnf.parser.Literal):
            return self.transform_literal(literal=rule.definition)
        elif isinstance(rule.definition, abnf.parser.Rule):
            return self.transform_rule(rule=rule.definition)
        else:
            raise AssertionError(f"Unhandled rule definition: {rule.definition}")


@require(lambda rule_cls: len(rule_cls.rules()) > 0)
def translate(rule_cls: Type[abnf.Rule]) -> Element:
    """Translate the ABNF rule to a regular expression."""
    regexp = ABNFTransformer().transform_rule(rule=rule_cls.rules()[0])  # type: ignore
    regexp = abnf_to_regexp.compression.compress(regexp)
    return regexp


class _Representer(Convertor[str]):
    """
    Represent a regular expression as a string.

    References are not expected in the input of this class.
    """

    # pylint: disable=missing-docstring,no-self-use

    def convert_concatenation(self, element: Concatenation) -> str:
        return "".join(self.visit(part) for part in element.elements)

    def convert_alternation(self, element: Alternation) -> str:
        return "".join(
            ("(", "|".join(self.visit(part) for part in element.elements), ")")
        )

    def convert_repetition(self, element: Repetition) -> str:
        if element.min_occurrences == 0 and element.max_occurrences is None:
            suffix = "*"
        elif element.min_occurrences == 0 and element.max_occurrences == 1:
            suffix = "?"
        elif (
            (element.min_occurrences is None or element.min_occurrences == 0)
            and element.max_occurrences is not None
            and element.max_occurrences > 0
        ):
            suffix = f"{{0,{element.max_occurrences}}}"
        elif (
            element.min_occurrences is not None
            and element.min_occurrences > 0
            and element.max_occurrences is None
        ):
            suffix = f"{{{element.min_occurrences},}}"
        else:
            suffix = f"{{{element.min_occurrences},{element.max_occurrences}}}"

        needs_parentheses = not isinstance(
            element.element, (Alternation, Range, CharacterClass)
        )

        result = (
            f"{self.visit(element.element)}{suffix}"
            if not needs_parentheses
            else f"({self.visit(element.element)}){suffix}"
        )

        return result

    def convert_case_insensitivity(self, element: CaseInsensitivity) -> str:
        return f"(?i:{self.visit(element.element)})"

    # noinspection PyMethodMayBeStatic
    def convert_literal(self, element: Literal) -> str:
        escaped_value = re.escape(element.value)
        assert isinstance(escaped_value, str)
        return escaped_value

    # noinspection PyMethodMayBeStatic
    def convert_range(self, element: Range) -> str:
        return "".join(
            (
                "[",
                escape_for_character_class(element.start),
                "-",
                escape_for_character_class(element.end),
                "]",
            )
        )

    def convert_character_class(self, element: CharacterClass) -> str:
        parts = []  # type: List[str]
        for subelement in element.elements:
            if isinstance(subelement, Range):
                parts.extend(
                    (
                        escape_for_character_class(subelement.start),
                        "-",
                        escape_for_character_class(subelement.end),
                    )
                )
            elif isinstance(subelement, Literal):
                parts.append(escape_for_character_class(subelement.value))
            else:
                raise NotImplementedError(
                    f"sub-element {subelement} in element {element}"
                )

        return "".join(["["] + parts + ["]"])

    def convert_reference(self, element: Reference) -> str:
        raise NotImplementedError(
            f"Unexpected reference in the regular expression: {element}; "
            f"are you using the correct visitor?"
        )


def represent(element: Element) -> str:
    """Represent the regular expression as a string pattern."""
    return _Representer().visit(element)
