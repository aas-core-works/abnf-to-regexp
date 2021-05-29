"""Provide building blocks for transformation of ABNF to something else."""
import abc
from typing import Union, Generic, Iterable, TypeVar

import regex as re

import abnf

from abnf_to_regexp.base import (
    Element,
    Repetition,
    Alternation,
    Concatenation,
    Range,
    CaseInsensitivity,
    Literal,
)

Parser = Union[
    abnf.Rule,
    abnf.parser.Literal,
    abnf.parser.Concatenation,
    abnf.parser.Option,
    abnf.parser.Alternation,
    abnf.parser.Repetition,
]

T = TypeVar("T")  # pylint: disable=invalid-name


class Transformer(abc.ABC, Generic[T]):
    """Transform an ABNF to something."""

    # pylint: disable=missing-docstring

    def transform_parser(self, parser: Parser) -> T:
        """Delegate the transformation of the ``parser``."""
        if isinstance(parser, abnf.Rule):
            return self.transform_rule(rule=parser)

        elif isinstance(parser, abnf.parser.Literal):
            return self.transform_literal(literal=parser)

        elif isinstance(parser, abnf.parser.Concatenation):
            return self.transform_concatenation(parsers=parser.parsers)

        elif isinstance(parser, abnf.parser.Option):
            return self.transform_option(option=parser)

        elif isinstance(parser, abnf.parser.Alternation):
            return self.transform_alternation(parsers=parser.parsers)

        elif isinstance(parser, abnf.parser.Repetition):
            return self.transform_repetition(
                repeat=parser.repeat, parser=parser.element
            )

        else:
            raise NotImplementedError(str(parser))

    @abc.abstractmethod
    def transform_option(self, option: abnf.parser.Option) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_alternation(self, parsers: Iterable[Parser]) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_repetition(self, repeat: abnf.parser.Repeat, parser: Parser) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_concatenation(self, parsers: Iterable[Parser]) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_literal(self, literal: abnf.parser.Literal) -> T:
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_rule(self, rule: abnf.Rule) -> T:
        raise NotImplementedError()


class TransformerToElement(Transformer[Element], abc.ABC):
    """Transform an ABNF to a regular expression."""

    # pylint: disable=missing-docstring,no-self-use

    def transform_option(self, option: abnf.parser.Option) -> Element:
        return Repetition(
            element=self.transform_parser(parser=option.alternation),
            min_occurrences=0,
            max_occurrences=1,
        )

    def transform_alternation(self, parsers: Iterable[Parser]) -> Element:
        return Alternation(
            elements=[self.transform_parser(parser=parser) for parser in parsers]
        )

    def transform_repetition(
        self, repeat: abnf.parser.Repeat, parser: Parser
    ) -> Element:
        return Repetition(
            element=self.transform_parser(parser=parser),
            min_occurrences=repeat.min,
            max_occurrences=repeat.max,
        )

    def transform_concatenation(self, parsers: Iterable[Parser]) -> Element:
        return Concatenation(
            elements=[self.transform_parser(parser) for parser in parsers]
        )

    def transform_literal(self, literal: abnf.parser.Literal) -> Element:
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

    @abc.abstractmethod
    def transform_rule(self, rule: abnf.Rule) -> Element:
        raise NotImplementedError()
