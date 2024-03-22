"""Provide building blocks for transformation of ABNF to something else."""

import abc
import bisect
import itertools
from typing import Union, Generic, Iterable, TypeVar, List, Tuple, Iterator

import abnf
import icontract
import regex as re

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
    abnf.parser.Parser,
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


# region Letter query

# NOTE (mristin, 2022-09-28):
# From: https://stackoverflow.com/questions/41698470/unicode-ranges-of-pl-plu-and-pll
#
# We ignore the unicode characters from the supplementary planes at the moment for
# the lack of time. Supporting the supplementary planes would have meant that we
# transpile the ranges from the StackOverflow answer to proper unicode ranges, as
# the answer operates on UTF-16 encoding.
_LETTER_CODES = [
    ("A", "Z"),
    ("a", "z"),
    ("\xaa", "\xaa"),
    ("\xb5", "\xb5"),
    ("\xba", "\xba"),
    ("\xc0", "\xd6"),
    ("\xd8", "\xf6"),
    ("\xf8", "\u02c1"),
    ("\u02c6", "\u02d1"),
    ("\u02e0", "\u02e4"),
    ("\u02ec", "\u02ec"),
    ("\u02ee", "\u02ee"),
    ("\u0370", "\u0374"),
    ("\u0376", "\u0377"),
    ("\u037a", "\u037d"),
    ("\u037f", "\u037f"),
    ("\u0386", "\u0386"),
    ("\u0388", "\u038a"),
    ("\u038c", "\u038c"),
    ("\u038e", "\u03a1"),
    ("\u03a3", "\u03f5"),
    ("\u03f7", "\u0481"),
    ("\u048a", "\u052f"),
    ("\u0531", "\u0556"),
    ("\u0559", "\u0559"),
    ("\u0560", "\u0588"),
    ("\u05d0", "\u05ea"),
    ("\u05ef", "\u05f2"),
    ("\u0620", "\u064a"),
    ("\u066e", "\u066f"),
    ("\u0671", "\u06d3"),
    ("\u06d5", "\u06d5"),
    ("\u06e5", "\u06e6"),
    ("\u06ee", "\u06ef"),
    ("\u06fa", "\u06fc"),
    ("\u06ff", "\u06ff"),
    ("\u0710", "\u0710"),
    ("\u0712", "\u072f"),
    ("\u074d", "\u07a5"),
    ("\u07b1", "\u07b1"),
    ("\u07ca", "\u07ea"),
    ("\u07f4", "\u07f5"),
    ("\u07fa", "\u07fa"),
    ("\u0800", "\u0815"),
    ("\u081a", "\u081a"),
    ("\u0824", "\u0824"),
    ("\u0828", "\u0828"),
    ("\u0840", "\u0858"),
    ("\u0860", "\u086a"),
    ("\u08a0", "\u08b4"),
    ("\u08b6", "\u08c7"),
    ("\u0904", "\u0939"),
    ("\u093d", "\u093d"),
    ("\u0950", "\u0950"),
    ("\u0958", "\u0961"),
    ("\u0971", "\u0980"),
    ("\u0985", "\u098c"),
    ("\u098f", "\u0990"),
    ("\u0993", "\u09a8"),
    ("\u09aa", "\u09b0"),
    ("\u09b2", "\u09b2"),
    ("\u09b6", "\u09b9"),
    ("\u09bd", "\u09bd"),
    ("\u09ce", "\u09ce"),
    ("\u09dc", "\u09dd"),
    ("\u09df", "\u09e1"),
    ("\u09f0", "\u09f1"),
    ("\u09fc", "\u09fc"),
    ("\u0a05", "\u0a0a"),
    ("\u0a0f", "\u0a10"),
    ("\u0a13", "\u0a28"),
    ("\u0a2a", "\u0a30"),
    ("\u0a32", "\u0a33"),
    ("\u0a35", "\u0a36"),
    ("\u0a38", "\u0a39"),
    ("\u0a59", "\u0a5c"),
    ("\u0a5e", "\u0a5e"),
    ("\u0a72", "\u0a74"),
    ("\u0a85", "\u0a8d"),
    ("\u0a8f", "\u0a91"),
    ("\u0a93", "\u0aa8"),
    ("\u0aaa", "\u0ab0"),
    ("\u0ab2", "\u0ab3"),
    ("\u0ab5", "\u0ab9"),
    ("\u0abd", "\u0abd"),
    ("\u0ad0", "\u0ad0"),
    ("\u0ae0", "\u0ae1"),
    ("\u0af9", "\u0af9"),
    ("\u0b05", "\u0b0c"),
    ("\u0b0f", "\u0b10"),
    ("\u0b13", "\u0b28"),
    ("\u0b2a", "\u0b30"),
    ("\u0b32", "\u0b33"),
    ("\u0b35", "\u0b39"),
    ("\u0b3d", "\u0b3d"),
    ("\u0b5c", "\u0b5d"),
    ("\u0b5f", "\u0b61"),
    ("\u0b71", "\u0b71"),
    ("\u0b83", "\u0b83"),
    ("\u0b85", "\u0b8a"),
    ("\u0b8e", "\u0b90"),
    ("\u0b92", "\u0b95"),
    ("\u0b99", "\u0b9a"),
    ("\u0b9c", "\u0b9c"),
    ("\u0b9e", "\u0b9f"),
    ("\u0ba3", "\u0ba4"),
    ("\u0ba8", "\u0baa"),
    ("\u0bae", "\u0bb9"),
    ("\u0bd0", "\u0bd0"),
    ("\u0c05", "\u0c0c"),
    ("\u0c0e", "\u0c10"),
    ("\u0c12", "\u0c28"),
    ("\u0c2a", "\u0c39"),
    ("\u0c3d", "\u0c3d"),
    ("\u0c58", "\u0c5a"),
    ("\u0c60", "\u0c61"),
    ("\u0c80", "\u0c80"),
    ("\u0c85", "\u0c8c"),
    ("\u0c8e", "\u0c90"),
    ("\u0c92", "\u0ca8"),
    ("\u0caa", "\u0cb3"),
    ("\u0cb5", "\u0cb9"),
    ("\u0cbd", "\u0cbd"),
    ("\u0cde", "\u0cde"),
    ("\u0ce0", "\u0ce1"),
    ("\u0cf1", "\u0cf2"),
    ("\u0d04", "\u0d0c"),
    ("\u0d0e", "\u0d10"),
    ("\u0d12", "\u0d3a"),
    ("\u0d3d", "\u0d3d"),
    ("\u0d4e", "\u0d4e"),
    ("\u0d54", "\u0d56"),
    ("\u0d5f", "\u0d61"),
    ("\u0d7a", "\u0d7f"),
    ("\u0d85", "\u0d96"),
    ("\u0d9a", "\u0db1"),
    ("\u0db3", "\u0dbb"),
    ("\u0dbd", "\u0dbd"),
    ("\u0dc0", "\u0dc6"),
    ("\u0e01", "\u0e30"),
    ("\u0e32", "\u0e33"),
    ("\u0e40", "\u0e46"),
    ("\u0e81", "\u0e82"),
    ("\u0e84", "\u0e84"),
    ("\u0e86", "\u0e8a"),
    ("\u0e8c", "\u0ea3"),
    ("\u0ea5", "\u0ea5"),
    ("\u0ea7", "\u0eb0"),
    ("\u0eb2", "\u0eb3"),
    ("\u0ebd", "\u0ebd"),
    ("\u0ec0", "\u0ec4"),
    ("\u0ec6", "\u0ec6"),
    ("\u0edc", "\u0edf"),
    ("\u0f00", "\u0f00"),
    ("\u0f40", "\u0f47"),
    ("\u0f49", "\u0f6c"),
    ("\u0f88", "\u0f8c"),
    ("\u1000", "\u102a"),
    ("\u103f", "\u103f"),
    ("\u1050", "\u1055"),
    ("\u105a", "\u105d"),
    ("\u1061", "\u1061"),
    ("\u1065", "\u1066"),
    ("\u106e", "\u1070"),
    ("\u1075", "\u1081"),
    ("\u108e", "\u108e"),
    ("\u10a0", "\u10c5"),
    ("\u10c7", "\u10c7"),
    ("\u10cd", "\u10cd"),
    ("\u10d0", "\u10fa"),
    ("\u10fc", "\u1248"),
    ("\u124a", "\u124d"),
    ("\u1250", "\u1256"),
    ("\u1258", "\u1258"),
    ("\u125a", "\u125d"),
    ("\u1260", "\u1288"),
    ("\u128a", "\u128d"),
    ("\u1290", "\u12b0"),
    ("\u12b2", "\u12b5"),
    ("\u12b8", "\u12be"),
    ("\u12c0", "\u12c0"),
    ("\u12c2", "\u12c5"),
    ("\u12c8", "\u12d6"),
    ("\u12d8", "\u1310"),
    ("\u1312", "\u1315"),
    ("\u1318", "\u135a"),
    ("\u1380", "\u138f"),
    ("\u13a0", "\u13f5"),
    ("\u13f8", "\u13fd"),
    ("\u1401", "\u166c"),
    ("\u166f", "\u167f"),
    ("\u1681", "\u169a"),
    ("\u16a0", "\u16ea"),
    ("\u16f1", "\u16f8"),
    ("\u1700", "\u170c"),
    ("\u170e", "\u1711"),
    ("\u1720", "\u1731"),
    ("\u1740", "\u1751"),
    ("\u1760", "\u176c"),
    ("\u176e", "\u1770"),
    ("\u1780", "\u17b3"),
    ("\u17d7", "\u17d7"),
    ("\u17dc", "\u17dc"),
    ("\u1820", "\u1878"),
    ("\u1880", "\u1884"),
    ("\u1887", "\u18a8"),
    ("\u18aa", "\u18aa"),
    ("\u18b0", "\u18f5"),
    ("\u1900", "\u191e"),
    ("\u1950", "\u196d"),
    ("\u1970", "\u1974"),
    ("\u1980", "\u19ab"),
    ("\u19b0", "\u19c9"),
    ("\u1a00", "\u1a16"),
    ("\u1a20", "\u1a54"),
    ("\u1aa7", "\u1aa7"),
    ("\u1b05", "\u1b33"),
    ("\u1b45", "\u1b4b"),
    ("\u1b83", "\u1ba0"),
    ("\u1bae", "\u1baf"),
    ("\u1bba", "\u1be5"),
    ("\u1c00", "\u1c23"),
    ("\u1c4d", "\u1c4f"),
    ("\u1c5a", "\u1c7d"),
    ("\u1c80", "\u1c88"),
    ("\u1c90", "\u1cba"),
    ("\u1cbd", "\u1cbf"),
    ("\u1ce9", "\u1cec"),
    ("\u1cee", "\u1cf3"),
    ("\u1cf5", "\u1cf6"),
    ("\u1cfa", "\u1cfa"),
    ("\u1d00", "\u1dbf"),
    ("\u1e00", "\u1f15"),
    ("\u1f18", "\u1f1d"),
    ("\u1f20", "\u1f45"),
    ("\u1f48", "\u1f4d"),
    ("\u1f50", "\u1f57"),
    ("\u1f59", "\u1f59"),
    ("\u1f5b", "\u1f5b"),
    ("\u1f5d", "\u1f5d"),
    ("\u1f5f", "\u1f7d"),
    ("\u1f80", "\u1fb4"),
    ("\u1fb6", "\u1fbc"),
    ("\u1fbe", "\u1fbe"),
    ("\u1fc2", "\u1fc4"),
    ("\u1fc6", "\u1fcc"),
    ("\u1fd0", "\u1fd3"),
    ("\u1fd6", "\u1fdb"),
    ("\u1fe0", "\u1fec"),
    ("\u1ff2", "\u1ff4"),
    ("\u1ff6", "\u1ffc"),
    ("\u2071", "\u2071"),
    ("\u207f", "\u207f"),
    ("\u2090", "\u209c"),
    ("\u2102", "\u2102"),
    ("\u2107", "\u2107"),
    ("\u210a", "\u2113"),
    ("\u2115", "\u2115"),
    ("\u2119", "\u211d"),
    ("\u2124", "\u2124"),
    ("\u2126", "\u2126"),
    ("\u2128", "\u2128"),
    ("\u212a", "\u212d"),
    ("\u212f", "\u2139"),
    ("\u213c", "\u213f"),
    ("\u2145", "\u2149"),
    ("\u214e", "\u214e"),
    ("\u2183", "\u2184"),
    ("\u2c00", "\u2c2e"),
    ("\u2c30", "\u2c5e"),
    ("\u2c60", "\u2ce4"),
    ("\u2ceb", "\u2cee"),
    ("\u2cf2", "\u2cf3"),
    ("\u2d00", "\u2d25"),
    ("\u2d27", "\u2d27"),
    ("\u2d2d", "\u2d2d"),
    ("\u2d30", "\u2d67"),
    ("\u2d6f", "\u2d6f"),
    ("\u2d80", "\u2d96"),
    ("\u2da0", "\u2da6"),
    ("\u2da8", "\u2dae"),
    ("\u2db0", "\u2db6"),
    ("\u2db8", "\u2dbe"),
    ("\u2dc0", "\u2dc6"),
    ("\u2dc8", "\u2dce"),
    ("\u2dd0", "\u2dd6"),
    ("\u2dd8", "\u2dde"),
    ("\u2e2f", "\u2e2f"),
    ("\u3005", "\u3006"),
    ("\u3031", "\u3035"),
    ("\u303b", "\u303c"),
    ("\u3041", "\u3096"),
    ("\u309d", "\u309f"),
    ("\u30a1", "\u30fa"),
    ("\u30fc", "\u30ff"),
    ("\u3105", "\u312f"),
    ("\u3131", "\u318e"),
    ("\u31a0", "\u31bf"),
    ("\u31f0", "\u31ff"),
    ("\u3400", "\u4dbf"),
    ("\u4e00", "\u9ffc"),
    ("\ua000", "\ua48c"),
    ("\ua4d0", "\ua4fd"),
    ("\ua500", "\ua60c"),
    ("\ua610", "\ua61f"),
    ("\ua62a", "\ua62b"),
    ("\ua640", "\ua66e"),
    ("\ua67f", "\ua69d"),
    ("\ua6a0", "\ua6e5"),
    ("\ua717", "\ua71f"),
    ("\ua722", "\ua788"),
    ("\ua78b", "\ua7bf"),
    ("\ua7c2", "\ua7ca"),
    ("\ua7f5", "\ua801"),
    ("\ua803", "\ua805"),
    ("\ua807", "\ua80a"),
    ("\ua80c", "\ua822"),
    ("\ua840", "\ua873"),
    ("\ua882", "\ua8b3"),
    ("\ua8f2", "\ua8f7"),
    ("\ua8fb", "\ua8fb"),
    ("\ua8fd", "\ua8fe"),
    ("\ua90a", "\ua925"),
    ("\ua930", "\ua946"),
    ("\ua960", "\ua97c"),
    ("\ua984", "\ua9b2"),
    ("\ua9cf", "\ua9cf"),
    ("\ua9e0", "\ua9e4"),
    ("\ua9e6", "\ua9ef"),
    ("\ua9fa", "\ua9fe"),
    ("\uaa00", "\uaa28"),
    ("\uaa40", "\uaa42"),
    ("\uaa44", "\uaa4b"),
    ("\uaa60", "\uaa76"),
    ("\uaa7a", "\uaa7a"),
    ("\uaa7e", "\uaaaf"),
    ("\uaab1", "\uaab1"),
    ("\uaab5", "\uaab6"),
    ("\uaab9", "\uaabd"),
    ("\uaac0", "\uaac0"),
    ("\uaac2", "\uaac2"),
    ("\uaadb", "\uaadd"),
    ("\uaae0", "\uaaea"),
    ("\uaaf2", "\uaaf4"),
    ("\uab01", "\uab06"),
    ("\uab09", "\uab0e"),
    ("\uab11", "\uab16"),
    ("\uab20", "\uab26"),
    ("\uab28", "\uab2e"),
    ("\uab30", "\uab5a"),
    ("\uab5c", "\uab69"),
    ("\uab70", "\uabe2"),
    ("\uac00", "\ud7a3"),
    ("\ud7b0", "\ud7c6"),
    ("\ud7cb", "\ud7fb"),
    ("\uf900", "\ufa6d"),
    ("\ufa70", "\ufad9"),
    ("\ufb00", "\ufb06"),
    ("\ufb13", "\ufb17"),
    ("\ufb1d", "\ufb1d"),
    ("\ufb1f", "\ufb28"),
    ("\ufb2a", "\ufb36"),
    ("\ufb38", "\ufb3c"),
    ("\ufb3e", "\ufb3e"),
    ("\ufb40", "\ufb41"),
    ("\ufb43", "\ufb44"),
    ("\ufb46", "\ufbb1"),
    ("\ufbd3", "\ufd3d"),
    ("\ufd50", "\ufd8f"),
    ("\ufd92", "\ufdc7"),
    ("\ufdf0", "\ufdfb"),
    ("\ufe70", "\ufe74"),
    ("\ufe76", "\ufefc"),
    ("\uff21", "\uff3a"),
    ("\uff41", "\uff5a"),
    ("\uff66", "\uffbe"),
    ("\uffc2", "\uffc7"),
    ("\uffca", "\uffcf"),
    ("\uffd2", "\uffd7"),
    ("\uffda", "\uffdc"),
    ("\U00010000", "\U0001000b"),
    ("\U0001000d", "\U00010026"),
    ("\U00010028", "\U0001003a"),
    ("\U0001003c", "\U0001003d"),
    ("\U0001003f", "\U0001004d"),
    ("\U00010050", "\U0001005d"),
    ("\U00010080", "\U000100fa"),
    ("\U00010280", "\U0001029c"),
    ("\U000102a0", "\U000102d0"),
    ("\U00010300", "\U0001031f"),
    ("\U0001032d", "\U00010340"),
    ("\U00010342", "\U00010349"),
    ("\U00010350", "\U00010375"),
    ("\U00010380", "\U0001039d"),
    ("\U000103a0", "\U000103c3"),
    ("\U000103c8", "\U000103cf"),
    ("\U00010400", "\U0001049d"),
    ("\U000104b0", "\U000104d3"),
    ("\U000104d8", "\U000104fb"),
    ("\U00010500", "\U00010527"),
    ("\U00010530", "\U00010563"),
    ("\U00010600", "\U00010736"),
    ("\U00010740", "\U00010755"),
    ("\U00010760", "\U00010767"),
    ("\U00010800", "\U00010805"),
    ("\U00010808", "\U00010808"),
    ("\U0001080a", "\U00010835"),
    ("\U00010837", "\U00010838"),
    ("\U0001083c", "\U0001083c"),
    ("\U0001083f", "\U00010855"),
    ("\U00010860", "\U00010876"),
    ("\U00010880", "\U0001089e"),
    ("\U000108e0", "\U000108f2"),
    ("\U000108f4", "\U000108f5"),
    ("\U00010900", "\U00010915"),
    ("\U00010920", "\U00010939"),
    ("\U00010980", "\U000109b7"),
    ("\U000109be", "\U000109bf"),
    ("\U00010a00", "\U00010a00"),
    ("\U00010a10", "\U00010a13"),
    ("\U00010a15", "\U00010a17"),
    ("\U00010a19", "\U00010a35"),
    ("\U00010a60", "\U00010a7c"),
    ("\U00010a80", "\U00010a9c"),
    ("\U00010ac0", "\U00010ac7"),
    ("\U00010ac9", "\U00010ae4"),
    ("\U00010b00", "\U00010b35"),
    ("\U00010b40", "\U00010b55"),
    ("\U00010b60", "\U00010b72"),
    ("\U00010b80", "\U00010b91"),
    ("\U00010c00", "\U00010c48"),
    ("\U00010c80", "\U00010cb2"),
    ("\U00010cc0", "\U00010cf2"),
    ("\U00010d00", "\U00010d23"),
    ("\U00010e80", "\U00010ea9"),
    ("\U00010eb0", "\U00010eb1"),
    ("\U00010f00", "\U00010f1c"),
    ("\U00010f27", "\U00010f27"),
    ("\U00010f30", "\U00010f45"),
    ("\U00010fb0", "\U00010fc4"),
    ("\U00010fe0", "\U00010ff6"),
    ("\U00011003", "\U00011037"),
    ("\U00011083", "\U000110af"),
    ("\U000110d0", "\U000110e8"),
    ("\U00011103", "\U00011126"),
    ("\U00011144", "\U00011144"),
    ("\U00011147", "\U00011147"),
    ("\U00011150", "\U00011172"),
    ("\U00011176", "\U00011176"),
    ("\U00011183", "\U000111b2"),
    ("\U000111c1", "\U000111c4"),
    ("\U000111da", "\U000111da"),
    ("\U000111dc", "\U000111dc"),
    ("\U00011200", "\U00011211"),
    ("\U00011213", "\U0001122b"),
    ("\U00011280", "\U00011286"),
    ("\U00011288", "\U00011288"),
    ("\U0001128a", "\U0001128d"),
    ("\U0001128f", "\U0001129d"),
    ("\U0001129f", "\U000112a8"),
    ("\U000112b0", "\U000112de"),
    ("\U00011305", "\U0001130c"),
    ("\U0001130f", "\U00011310"),
    ("\U00011313", "\U00011328"),
    ("\U0001132a", "\U00011330"),
    ("\U00011332", "\U00011333"),
    ("\U00011335", "\U00011339"),
    ("\U0001133d", "\U0001133d"),
    ("\U00011350", "\U00011350"),
    ("\U0001135d", "\U00011361"),
    ("\U00011400", "\U00011434"),
    ("\U00011447", "\U0001144a"),
    ("\U0001145f", "\U00011461"),
    ("\U00011480", "\U000114af"),
    ("\U000114c4", "\U000114c5"),
    ("\U000114c7", "\U000114c7"),
    ("\U00011580", "\U000115ae"),
    ("\U000115d8", "\U000115db"),
    ("\U00011600", "\U0001162f"),
    ("\U00011644", "\U00011644"),
    ("\U00011680", "\U000116aa"),
    ("\U000116b8", "\U000116b8"),
    ("\U00011700", "\U0001171a"),
    ("\U00011800", "\U0001182b"),
    ("\U000118a0", "\U000118df"),
    ("\U000118ff", "\U00011906"),
    ("\U00011909", "\U00011909"),
    ("\U0001190c", "\U00011913"),
    ("\U00011915", "\U00011916"),
    ("\U00011918", "\U0001192f"),
    ("\U0001193f", "\U0001193f"),
    ("\U00011941", "\U00011941"),
    ("\U000119a0", "\U000119a7"),
    ("\U000119aa", "\U000119d0"),
    ("\U000119e1", "\U000119e1"),
    ("\U000119e3", "\U000119e3"),
    ("\U00011a00", "\U00011a00"),
    ("\U00011a0b", "\U00011a32"),
    ("\U00011a3a", "\U00011a3a"),
    ("\U00011a50", "\U00011a50"),
    ("\U00011a5c", "\U00011a89"),
    ("\U00011a9d", "\U00011a9d"),
    ("\U00011ac0", "\U00011af8"),
    ("\U00011c00", "\U00011c08"),
    ("\U00011c0a", "\U00011c2e"),
    ("\U00011c40", "\U00011c40"),
    ("\U00011c72", "\U00011c8f"),
    ("\U00011d00", "\U00011d06"),
    ("\U00011d08", "\U00011d09"),
    ("\U00011d0b", "\U00011d30"),
    ("\U00011d46", "\U00011d46"),
    ("\U00011d60", "\U00011d65"),
    ("\U00011d67", "\U00011d68"),
    ("\U00011d6a", "\U00011d89"),
    ("\U00011d98", "\U00011d98"),
    ("\U00011ee0", "\U00011ef2"),
    ("\U00011fb0", "\U00011fb0"),
    ("\U00012000", "\U00012399"),
    ("\U00012480", "\U00012543"),
    ("\U00013000", "\U0001342e"),
    ("\U00014400", "\U00014646"),
    ("\U00016800", "\U00016a38"),
    ("\U00016a40", "\U00016a5e"),
    ("\U00016ad0", "\U00016aed"),
    ("\U00016b00", "\U00016b2f"),
    ("\U00016b40", "\U00016b43"),
    ("\U00016b63", "\U00016b77"),
    ("\U00016b7d", "\U00016b8f"),
    ("\U00016e40", "\U00016e7f"),
    ("\U00016f00", "\U00016f4a"),
    ("\U00016f50", "\U00016f50"),
    ("\U00016f93", "\U00016f9f"),
    ("\U00016fe0", "\U00016fe1"),
    ("\U00016fe3", "\U00016fe3"),
    ("\U00017000", "\U000187f7"),
    ("\U00018800", "\U00018cd5"),
    ("\U00018d00", "\U00018d08"),
    ("\U0001b000", "\U0001b11e"),
    ("\U0001b150", "\U0001b152"),
    ("\U0001b164", "\U0001b167"),
    ("\U0001b170", "\U0001b2fb"),
    ("\U0001bc00", "\U0001bc6a"),
    ("\U0001bc70", "\U0001bc7c"),
    ("\U0001bc80", "\U0001bc88"),
    ("\U0001bc90", "\U0001bc99"),
    ("\U0001d400", "\U0001d454"),
    ("\U0001d456", "\U0001d49c"),
    ("\U0001d49e", "\U0001d49f"),
    ("\U0001d4a2", "\U0001d4a2"),
    ("\U0001d4a5", "\U0001d4a6"),
    ("\U0001d4a9", "\U0001d4ac"),
    ("\U0001d4ae", "\U0001d4b9"),
    ("\U0001d4bb", "\U0001d4bb"),
    ("\U0001d4bd", "\U0001d4c3"),
    ("\U0001d4c5", "\U0001d505"),
    ("\U0001d507", "\U0001d50a"),
    ("\U0001d50d", "\U0001d514"),
    ("\U0001d516", "\U0001d51c"),
    ("\U0001d51e", "\U0001d539"),
    ("\U0001d53b", "\U0001d53e"),
    ("\U0001d540", "\U0001d544"),
    ("\U0001d546", "\U0001d546"),
    ("\U0001d54a", "\U0001d550"),
    ("\U0001d552", "\U0001d6a5"),
    ("\U0001d6a8", "\U0001d6c0"),
    ("\U0001d6c2", "\U0001d6da"),
    ("\U0001d6dc", "\U0001d6fa"),
    ("\U0001d6fc", "\U0001d714"),
    ("\U0001d716", "\U0001d734"),
    ("\U0001d736", "\U0001d74e"),
    ("\U0001d750", "\U0001d76e"),
    ("\U0001d770", "\U0001d788"),
    ("\U0001d78a", "\U0001d7a8"),
    ("\U0001d7aa", "\U0001d7c2"),
    ("\U0001d7c4", "\U0001d7cb"),
    ("\U0001e100", "\U0001e12c"),
    ("\U0001e137", "\U0001e13d"),
    ("\U0001e14e", "\U0001e14e"),
    ("\U0001e2c0", "\U0001e2eb"),
    ("\U0001e800", "\U0001e8c4"),
    ("\U0001e900", "\U0001e943"),
    ("\U0001e94b", "\U0001e94b"),
    ("\U0001ee00", "\U0001ee03"),
    ("\U0001ee05", "\U0001ee1f"),
    ("\U0001ee21", "\U0001ee22"),
    ("\U0001ee24", "\U0001ee24"),
    ("\U0001ee27", "\U0001ee27"),
    ("\U0001ee29", "\U0001ee32"),
    ("\U0001ee34", "\U0001ee37"),
    ("\U0001ee39", "\U0001ee39"),
    ("\U0001ee3b", "\U0001ee3b"),
    ("\U0001ee42", "\U0001ee42"),
    ("\U0001ee47", "\U0001ee47"),
    ("\U0001ee49", "\U0001ee49"),
    ("\U0001ee4b", "\U0001ee4b"),
    ("\U0001ee4d", "\U0001ee4f"),
    ("\U0001ee51", "\U0001ee52"),
    ("\U0001ee54", "\U0001ee54"),
    ("\U0001ee57", "\U0001ee57"),
    ("\U0001ee59", "\U0001ee59"),
    ("\U0001ee5b", "\U0001ee5b"),
    ("\U0001ee5d", "\U0001ee5d"),
    ("\U0001ee5f", "\U0001ee5f"),
    ("\U0001ee61", "\U0001ee62"),
    ("\U0001ee64", "\U0001ee64"),
    ("\U0001ee67", "\U0001ee6a"),
    ("\U0001ee6c", "\U0001ee72"),
    ("\U0001ee74", "\U0001ee77"),
    ("\U0001ee79", "\U0001ee7c"),
    ("\U0001ee7e", "\U0001ee7e"),
    ("\U0001ee80", "\U0001ee89"),
    ("\U0001ee8b", "\U0001ee9b"),
    ("\U0001eea1", "\U0001eea3"),
    ("\U0001eea5", "\U0001eea9"),
    ("\U0001eeab", "\U0001eebb"),
    ("\U00020000", "\U0002a6dd"),
    ("\U0002a700", "\U0002b734"),
    ("\U0002b740", "\U0002b81d"),
    ("\U0002b820", "\U0002cea1"),
    ("\U0002ceb0", "\U0002ebe0"),
    ("\U0002f800", "\U0002fa1d"),
    ("\U00030000", "\U0003134a"),
]


def _char_ranges_to_ord_ranges(lst: List[Tuple[str, str]]) -> List[Tuple[int, int]]:
    """Convert the character ranges into ordinal ranges for easier manipulation."""
    result = []  # type: List[Tuple[int, int]]
    for start, end in lst:
        assert len(start) == 1, f"Expected a single character, but got {start!r}"
        assert len(end) == 1, f"Expected a single character, but got {end!r}"

        result.append((ord(start), ord(end)))

    return result


_LETTER_ORD_RANGES = sorted(_char_ranges_to_ord_ranges(_LETTER_CODES))


def pairwise(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
    """
    Iterate pairwise over an iterable.

    ``pairwise('ABCDEFG') --> AB BC CD DE EF FG``
    """
    fst, snd = itertools.tee(iterable)
    next(snd, None)
    return zip(fst, snd)


assert all(start <= end for start, end in _LETTER_ORD_RANGES)
assert all(
    end1 < start2 for (_, end1), (start2, _) in pairwise(_LETTER_ORD_RANGES)
), "No overlapping ranges"

_LETTER_ORD_RANGE_STARTS = [start for start, _ in _LETTER_ORD_RANGES]
_LETTER_ORD_RANGE_ENDS = [end for _, end in _LETTER_ORD_RANGES]


@icontract.require(lambda start_ord, end_ord: start_ord <= end_ord)
def _range_overlaps_with_a_letter_range(start_ord: int, end_ord: int) -> bool:
    """
    Check whether the range ``start_ord, end_ord`` overlaps with a letter range.

    The range ``start_ord, end_ord`` is considered inclusive.

    The ordinal values of start and end are given as unicode values from ``ord(.)``
    applied on the start and end characters of the range.
    """
    # NOTE (mristin, 2022-09-28):
    # Handle the edge cases first, so that the logic below becomes a bit simpler.

    assert len(_LETTER_ORD_RANGES) > 0

    # ``start`` is after the end of all the letter ranges?
    if start_ord > _LETTER_ORD_RANGES[-1][1]:
        return False

    # ``end`` is before the start of all the letter ranges?
    if end_ord < _LETTER_ORD_RANGES[0][0]:
        return False

    # Find the interval with the end *at* or *after* the ``start``
    i = bisect.bisect_left(_LETTER_ORD_RANGE_ENDS, start_ord)

    # Since we checked that ``start`` is before at least one end of a letter range,
    # the ``i`` refers to the range whose end >= ``start``.
    range_start_ord, range_end_ord = _LETTER_ORD_RANGES[i]
    if start_ord <= range_end_ord and end_ord >= range_start_ord:
        return True

    # Find the interval with the start *at* or *before* the ``end``
    i = bisect.bisect_left(_LETTER_ORD_RANGE_STARTS, end_ord)

    # Since we checked that ``end`` comes after at least one letter range,
    # we know that we will have a hit here, and ``i`` points to the range whose
    # start >= ``end``.
    range_start_ord, range_end_ord = _LETTER_ORD_RANGES[i]
    if start_ord <= range_end_ord and end_ord >= range_start_ord:
        return True

    return False


# endregion


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
        if (
            isinstance(literal.pattern, tuple)
            and len(literal.pattern) == 2
            and isinstance(literal.pattern[0], str)
            and isinstance(literal.pattern[1], str)
        ):
            start, end = literal.pattern

            result = Range(start=start, end=end)  # type: Element

        elif isinstance(literal.pattern, str):
            assert isinstance(literal.pattern, str)

            if isinstance(literal.value, str):
                result = Literal(value=literal.value)

            elif (
                isinstance(literal.value, tuple)
                and len(literal.value) == 2
                and isinstance(literal.value[0], str)
                and isinstance(literal.value[1], str)
            ):
                start, end = literal.value

                result = Range(start=start, end=end)
            else:
                raise AssertionError(f"Unexpected literal value: {literal.value}")
        else:
            raise AssertionError(f"Unexpected literal pattern: {literal.pattern}")

        if not literal.case_sensitive:
            # NOTE (mristin, 2022-09-28):
            # The ABNF is case-insensitive by default. However, adding case-sensitivity
            # checks pollutes regular expressions unnecessarily if there are no letters
            # involved.
            #
            # Therefore, we explicitly check that the literal or the range involves
            # any letter before we enforce case-insensitivity in the regular expression.

            if isinstance(result, Range):
                assert len(result.start) == 1
                assert len(result.end) == 1

                if _range_overlaps_with_a_letter_range(
                    start_ord=ord(result.start), end_ord=ord(result.end)
                ):
                    result = CaseInsensitivity(element=result)

            elif isinstance(result, Literal):
                if re.search(r"\p{L}", result.value):
                    result = CaseInsensitivity(element=result)

            else:
                raise AssertionError(f"Unexpected result: {result}")

        return result

    @abc.abstractmethod
    def transform_rule(self, rule: abnf.Rule) -> Element:
        raise NotImplementedError()
