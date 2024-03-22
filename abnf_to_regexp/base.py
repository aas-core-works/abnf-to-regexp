"""Provide base building blocks for the regular expressions."""

import abc
from typing import Iterable, Optional, Union, TypeVar, Generic

from icontract import require


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

    def __repr__(self) -> str:
        return f"Literal({self.value!r})"


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


class Reference(Element):
    """Represent a reference to another expression which should be embedded."""

    def __init__(self, name: str) -> None:
        self.name = name


class Transformer:
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
        elif isinstance(element, Reference):
            return self.transform_reference(element)
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

    # noinspection PyMethodMayBeStatic
    def transform_literal(self, element: Literal) -> Element:
        return element

    # noinspection PyMethodMayBeStatic
    def transform_range(self, element: Range) -> Element:
        return element

    # noinspection PyMethodMayBeStatic
    def transform_character_class(self, element: CharacterClass) -> Element:
        return element

    # noinspection PyMethodMayBeStatic
    def transform_reference(self, element: Reference) -> Element:
        return element

    def transform_default(self, element: Element) -> Element:
        raise AssertionError(f"Unhandled transformation of an element: {element}")


T = TypeVar("T")  # pylint: disable=invalid-name


class Convertor(Generic[T]):
    """Convert recursively a regular expression to something else."""

    # pylint: disable=missing-docstring,no-self-use

    def visit(self, element: Element) -> T:
        if isinstance(element, Concatenation):
            return self.convert_concatenation(element)
        elif isinstance(element, Alternation):
            return self.convert_alternation(element)
        elif isinstance(element, Repetition):
            return self.convert_repetition(element)
        elif isinstance(element, CaseInsensitivity):
            return self.convert_case_insensitivity(element)
        elif isinstance(element, Literal):
            return self.convert_literal(element)
        elif isinstance(element, Range):
            return self.convert_range(element)
        elif isinstance(element, CharacterClass):
            return self.convert_character_class(element)
        elif isinstance(element, Reference):
            return self.convert_reference(element)
        else:
            return self.convert_default(element)

    def convert_concatenation(self, element: Concatenation) -> T:
        raise NotImplementedError()

    def convert_alternation(self, element: Alternation) -> T:
        raise NotImplementedError()

    def convert_repetition(self, element: Repetition) -> T:
        raise NotImplementedError()

    def convert_case_insensitivity(self, element: CaseInsensitivity) -> T:
        raise NotImplementedError()

    def convert_literal(self, element: Literal) -> T:
        raise NotImplementedError()

    def convert_range(self, element: Range) -> T:
        raise NotImplementedError()

    def convert_character_class(self, element: CharacterClass) -> T:
        raise NotImplementedError()

    def convert_reference(self, element: Reference) -> T:
        raise NotImplementedError()

    def convert_default(self, element: Element) -> T:
        raise AssertionError(f"Unhandled conversion of an element: {element}")


class Visitor:
    """Visit recursively a regular expression."""

    # pylint: disable=missing-docstring,no-self-use

    def visit(self, element: Element) -> None:
        if isinstance(element, Concatenation):
            return self.visit_concatenation(element)
        elif isinstance(element, Alternation):
            return self.visit_alternation(element)
        elif isinstance(element, Repetition):
            return self.visit_repetition(element)
        elif isinstance(element, CaseInsensitivity):
            return self.visit_case_insensitivity(element)
        elif isinstance(element, Literal):
            return self.visit_literal(element)
        elif isinstance(element, Range):
            return self.visit_range(element)
        elif isinstance(element, CharacterClass):
            return self.visit_character_class(element)
        elif isinstance(element, Reference):
            return self.visit_reference(element)
        else:
            return self.visit_default(element)

    def visit_concatenation(self, element: Concatenation) -> None:
        for subelement in element.elements:
            self.visit(subelement)

    def visit_alternation(self, element: Alternation) -> None:
        for subelement in element.elements:
            self.visit(subelement)

    def visit_repetition(self, element: Repetition) -> None:
        self.visit(element.element)

    def visit_case_insensitivity(self, element: CaseInsensitivity) -> None:
        self.visit(element.element)

    # noinspection PyMethodMayBeStatic
    def visit_literal(self, element: Literal) -> None:
        pass

    # noinspection PyMethodMayBeStatic
    def visit_range(self, element: Range) -> None:
        pass

    # noinspection PyMethodMayBeStatic
    def visit_character_class(self, element: CharacterClass) -> None:
        pass

    # noinspection PyMethodMayBeStatic
    def visit_reference(self, element: Reference) -> None:
        pass

    def visit_default(self, element: Element) -> None:
        raise AssertionError(f"Unhandled visitation of an element: {element}")
