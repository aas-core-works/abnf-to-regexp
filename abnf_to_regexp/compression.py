"""Compress regular expressions to an equivalent shorter form."""

from typing import List, Union

import regex as re

from abnf_to_regexp.base import (
    Transformer,
    Alternation,
    Element,
    Literal,
    Range,
    CharacterClass,
    CaseInsensitivity,
)


class _MergeAlternations(Transformer):
    def transform_alternation(self, element: Alternation) -> Element:
        transformed_subelements = [
            self.transform(subelement) for subelement in element.elements
        ]

        if all(
            isinstance(subelement, Alternation)
            for subelement in transformed_subelements
        ):
            merged = []  # type: List[Element]
            for subelement in transformed_subelements:
                assert isinstance(subelement, Alternation)
                merged.extend(subelement.elements)

            return Alternation(elements=merged)

        return element


class _MergeAlternationsOfCharacterClasses(Transformer):
    def transform_alternation(self, element: Alternation) -> Element:
        transformed_subelements = [
            self.transform(subelement) for subelement in element.elements
        ]

        new_subelements = []  # type: List[Element]

        accumulator = []  # type: List[Union[Range, Literal]]
        for subelement in transformed_subelements:
            if (
                isinstance(subelement, Literal) and len(subelement.value) > 1
            ) or not isinstance(subelement, (Literal, Range, CharacterClass)):
                if len(accumulator) > 0:
                    if len(accumulator) > 1:
                        new_subelements.append(CharacterClass(elements=accumulator))
                    else:
                        new_subelements.append(accumulator[0])

                    accumulator = []

                new_subelements.append(subelement)

            else:
                if isinstance(subelement, Literal):
                    assert len(subelement.value) == 1
                    accumulator.append(subelement)
                elif isinstance(subelement, Range):
                    accumulator.append(subelement)
                elif isinstance(subelement, CharacterClass):
                    accumulator.extend(subelement.elements)
                else:
                    raise AssertionError(subelement)

        if len(accumulator) > 0:
            if len(accumulator) > 1:
                new_subelements.append(CharacterClass(elements=accumulator))
            else:
                new_subelements.append(accumulator[0])

        if len(new_subelements) == 1:
            return new_subelements[0]

        return Alternation(elements=new_subelements)


class _SingleLetterCaseInsensitiveToRange(Transformer):
    def transform_case_insensitivity(self, element: CaseInsensitivity) -> Element:
        transformed_subelement = self.transform(element.element)

        if (
            isinstance(transformed_subelement, Literal)
            and len(transformed_subelement.value) == 1
            and re.match(r"\p{L}", transformed_subelement.value)
        ):
            return CharacterClass(
                elements=[
                    Literal(transformed_subelement.value.lower()),
                    Literal(transformed_subelement.value.upper()),
                ]
            )

        return transformed_subelement


def compress(element: Element) -> Element:
    """Apply multiple compressions to the element to obtain a more readable regexp."""
    element = _MergeAlternationsOfCharacterClasses().transform(element)
    element = _MergeAlternations().transform(element)
    element = _SingleLetterCaseInsensitiveToRange().transform(element)

    return element
