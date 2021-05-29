"""Compress regular expressions to an equivalent shorter form."""
from typing import List, Union

from abnf_to_regexp.base import (
    Transformer,
    Alternation,
    Element,
    Literal,
    Range,
    CharacterClass,
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


def compress(element: Element) -> Element:
    """Apply multiple compressions to the element to obtain a more readable regexp."""
    element = _MergeAlternationsOfCharacterClasses().transform(element)
    element = _MergeAlternations().transform(element)

    return element
