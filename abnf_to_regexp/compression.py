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

        can_merge = True
        for subelement in transformed_subelements:
            if not isinstance(subelement, (Literal, Range, CharacterClass)):
                can_merge = False
                break

            if isinstance(subelement, Literal) and len(subelement.value) > 1:
                can_merge = False
                break

        if not can_merge:
            return Alternation(elements=transformed_subelements)

        merged = []  # type: List[Union[Range, Literal]]
        for subelement in transformed_subelements:
            if isinstance(subelement, CharacterClass):
                merged.extend(subelement.elements)
            elif isinstance(subelement, Literal):
                merged.append(subelement)
            elif isinstance(subelement, Range):
                merged.append(subelement)
            else:
                raise AssertionError(str(subelement))

        return CharacterClass(elements=merged)


def compress(element: Element) -> Element:
    """Apply multiple compressions to the element to obtain a more readable regexp."""
    element = _MergeAlternationsOfCharacterClasses().transform(element)
    element = _MergeAlternations().transform(element)

    return element
