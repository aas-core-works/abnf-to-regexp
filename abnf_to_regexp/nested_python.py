"""Translate an ABNF to a code snippet of Python."""

import collections
import enum
import io
import string
from typing import (
    Mapping,
    Type,
    MutableMapping,
    List,
    Sequence,
    Optional,
    Tuple,
)

import abnf
import regex as re
from icontract import require, ensure
import sortedcontainers

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
    Reference,
    Transformer,
    Visitor,
)
from abnf_to_regexp.representation import escape_for_character_class

# Short-circuit the rules from RFC 5234 to regular expressions
_RFC_5234 = {
    "CR": Literal("\x0D"),
    "LF": Literal("\x0A"),
    "CRLF": Literal("\x0D\x0A"),
    "HTAB": Literal("\x09"),
    "DQUOTE": Literal('"'),
    "SP": Literal(" "),
    "WSP": CharacterClass([Literal(" "), Literal("\x09")]),
    "VCHAR": Range(start="\x21", end="\x7E"),
    "ALPHA": CharacterClass(
        elements=[Range(start="a", end="z"), Range(start="A", end="Z")]
    ),
    "DIGIT": Range(start="0", end="9"),
    "HEXDIG": CharacterClass(
        elements=[
            Range(start="0", end="9"),
            Range(start="A", end="F"),
            Range(start="a", end="f"),
        ]
    ),
    "BIT": CharacterClass(elements=[Literal(value="0"), Literal(value="1")]),
}


class ABNFTransformer(abnf_to_regexp.abnf_transformation.TransformerToElement):
    """Translate ABNF rule to a regular expressions including references."""

    def transform_rule(self, rule: abnf.Rule) -> Element:
        # Short-circuit the rules from RFC 5234
        short_circuited = _RFC_5234.get(rule.name, None)
        if short_circuited is not None:
            return short_circuited
        else:
            return Reference(name=rule.name)


class _RenameRules(Transformer):
    def __init__(self, mapping: Mapping[str, str]) -> None:
        self.mapping = mapping

    def transform_reference(self, element: Reference) -> Element:
        if element.name not in self.mapping:
            raise KeyError(
                f"The reference to a rule name has not been mapped: {element.name!r}"
            )

        return Reference(name=self.mapping[element.name])


@ensure(lambda result: all(name.isidentifier() for name in result[0]))
def _rename_rules_to_variable_identifiers(
    table: Mapping[str, Element]
) -> Tuple["collections.OrderedDict[str, Element]", Mapping[str, str]]:
    """
    Rename all rules and the references to make them valid variable identifiers.

    Return (table with renamed rules, mapping original name -> valid identifier).
    """
    mapping = dict()  # type: MutableMapping[str, str]
    for name in table:
        proposed_name = re.sub("[^a-zA-Z_0-9]", "_", name).lower()
        i = 1
        while proposed_name in mapping:
            proposed_name = proposed_name + str(i)
            i += 1

        mapping[name] = proposed_name

    transformer = _RenameRules(mapping=mapping)

    new_table = collections.OrderedDict()  # type: collections.OrderedDict[str, Element]
    for name, element in table.items():
        new_table[mapping[name]] = transformer.transform(element)

    return new_table, mapping


class _ReferenceVisitor(Visitor):
    """List all the references in the given regular expression."""

    def __init__(self) -> None:
        self.references = []  # type: List[str]

    def visit_reference(self, element: Reference) -> None:
        self.references.append(element.name)


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def _topological_sort(
    graph: Mapping[str, List[str]]
) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Figure out the dependency graph using the topological sort.

    Return None if there is a cycle.
    """
    # See https://en.wikipedia.org/wiki/Topological_sorting#Depth-first%20search
    trace = []  # type: List[str]
    # We use sorted containers to avoid non-deterministic behavior.
    identifiers_without_permanent_marks = sortedcontainers.SortedSet(graph.keys())
    permanent_marks = sortedcontainers.SortedSet()  # Set[str]
    temporary_marks = sortedcontainers.SortedSet()  # Set[str]

    visited_more_than_once = None  # type: Optional[str]

    def visit(an_identifier: str) -> None:
        nonlocal visited_more_than_once
        nonlocal trace

        if visited_more_than_once:
            return

        if an_identifier in permanent_marks:
            return

        if an_identifier in temporary_marks:
            visited_more_than_once = an_identifier
            return

        temporary_marks.add(an_identifier)

        for reference in graph[an_identifier]:
            visit(reference)

        temporary_marks.remove(an_identifier)
        permanent_marks.add(an_identifier)
        identifiers_without_permanent_marks.remove(an_identifier)
        trace.insert(0, an_identifier)

    while len(identifiers_without_permanent_marks) > 0 and not visited_more_than_once:
        visit(identifiers_without_permanent_marks[0])

    if visited_more_than_once:
        return None, visited_more_than_once

    return trace, None


def _reorder_table_by_dependencies(
    table: "collections.OrderedDict[str, Element]",
) -> Tuple[Optional["collections.OrderedDict[str, Element]"], Optional[str]]:
    """
    Order the table so that the rules are defined after their dependencies.

    Return (re-ordered table, identifier where a cycle has been observed)
    """
    # We construct the graph using a sorted dict to avoid non-deterministic
    # behavior.
    graph = sortedcontainers.SortedDict()  # type: MutableMapping[str, List[str]]
    for identifier, regexp in table.items():
        visitor = _ReferenceVisitor()
        visitor.visit(regexp)

        graph[identifier] = visitor.references

    trace, duplicate_visit = _topological_sort(graph=graph)
    if duplicate_visit is not None:
        return None, duplicate_visit

    assert trace is not None

    # Change the order
    new_table = collections.OrderedDict()  # type: collections.OrderedDict[str, Element]
    for identifier in reversed(trace):
        new_table[identifier] = table[identifier]

    return new_table, None


@ensure(lambda result: (result[0] is None) ^ (result[1] is None))
def translate(
    rule_cls: Type[abnf.Rule],
) -> Tuple[Optional["collections.OrderedDict[str, Element]"], Optional[str]]:
    """Translate the ABNF rule to a regular expression."""
    table = collections.OrderedDict()  # type: collections.OrderedDict[str, Element]

    transformer = ABNFTransformer()

    for rule in rule_cls.rules():  # type: ignore
        table[rule.name] = abnf_to_regexp.compression.compress(
            transformer.transform_parser(rule.definition)
        )

    table, name_mapping = _rename_rules_to_variable_identifiers(table=table)

    reordered_table, duplicate_visit = _reorder_table_by_dependencies(table=table)
    if duplicate_visit:
        return (
            None,
            f"You have a cycle in your ABNF. "
            f"The rule has been visited "
            f"more than once: {name_mapping[duplicate_visit]}",
        )
    assert reordered_table is not None

    return reordered_table, None


class _TokenKind(enum.Enum):
    TEXT = 0
    REFERENCE = 1
    BREAK_POINT = 3


class _Token:
    """Capture a part of the string representing a regular expression."""

    # fmt: off
    @require(
        lambda value, kind:
        not (kind == _TokenKind.BREAK_POINT) or value == ''
    )
    # fmt: on
    def __init__(self, value: str, kind: _TokenKind) -> None:
        self.value = value
        self.kind = kind


class _Stream:
    """Write tokens as you visit the regular expression tree."""

    def __init__(self) -> None:
        """Initialize with the given values."""
        self.tokens = []  # type: List[_Token]

    def write_text(self, text: str) -> None:
        """Add a text token."""
        self.tokens.append(_Token(value=text, kind=_TokenKind.TEXT))

    def mark_breakpoint(self) -> None:
        """Mark the position where line can be broken."""
        self.tokens.append(_Token(value="", kind=_TokenKind.BREAK_POINT))

    def write_reference(self, name: str) -> None:
        """Add a reference token."""
        self.tokens.append(_Token(value=name, kind=_TokenKind.REFERENCE))


class _Representer(Visitor):
    """
    Represent a regular expression as a stream of tokens.

    Please see ``.stream`` for the result.
    """

    def __init__(self) -> None:
        self.stream = _Stream()

    def visit_concatenation(self, element: Concatenation) -> None:
        for i, subelement in enumerate(element.elements):
            if i > 0:
                self.stream.mark_breakpoint()

            self.visit(subelement)

    def visit_alternation(self, element: Alternation) -> None:
        self.stream.write_text("(")

        for i, subelement in enumerate(element.elements):
            if i > 0:
                self.stream.write_text("|")
                self.stream.mark_breakpoint()

            self.visit(subelement)

        self.stream.write_text(")")

    def visit_repetition(self, element: Repetition) -> None:
        if element.min_occurrences == 0 and element.max_occurrences is None:
            suffix = "*"
        elif element.min_occurrences == 0 and element.max_occurrences == 1:
            suffix = "?"
        elif (
            (element.min_occurrences is None or element.min_occurrences == 0)
            and element.max_occurrences is not None
            and element.max_occurrences > 0
        ):
            suffix = f"{{,{element.max_occurrences}}}"
        elif (
            element.min_occurrences is not None
            and element.min_occurrences > 0
            and element.max_occurrences is None
        ):
            if element.min_occurrences == 1:
                suffix = "+"
            else:
                suffix = f"{{{element.min_occurrences},}}"
        elif (
            element.min_occurrences is not None
            and element.max_occurrences is not None
            and element.min_occurrences == element.max_occurrences
        ):
            suffix = f"{{{element.min_occurrences}}}"
        else:
            suffix = f"{{{element.min_occurrences},{element.max_occurrences}}}"

        needs_parentheses = not isinstance(
            element.element, (Alternation, Range, CharacterClass)
        )

        if needs_parentheses:
            self.stream.write_text("(")

        self.visit(element.element)

        if needs_parentheses:
            self.stream.write_text(f"){suffix}")
        else:
            self.stream.write_text(suffix)

    def visit_case_insensitivity(self, element: CaseInsensitivity) -> None:
        self.stream.write_text("(?i:")
        self.visit(element.element)
        self.stream.write_text(")")

    _NO_NEED_TO_ESCAPE_RE = re.compile(r"[a-zA-Z_0-9\-]*")

    def visit_literal(self, element: Literal) -> None:
        # ``re.escape`` is a bit too conservative and produces unreadable regular
        # expressions. To make the expressions more readable, we avoid escaping
        # the cases where we are sure no escapes are necessary.
        if _Representer._NO_NEED_TO_ESCAPE_RE.fullmatch(element.value):
            self.stream.write_text(element.value)
        else:
            for character in element.value:
                if character not in string.printable and ord(character) <= 255:
                    escaped_value = f"\\x{ord(character):02x}"
                elif 255 < ord(character) < 0x10000:
                    escaped_value = f"\\u{ord(character):04x}"
                elif 0x10000 <= ord(character) <= 0x10FFFF:
                    escaped_value = f"\\U{ord(character):08x}"
                else:
                    escaped_value = re.escape(character)

                assert isinstance(escaped_value, str)

                self.stream.write_text(escaped_value)

    def visit_range(self, element: Range) -> None:
        self.stream.write_text(
            "".join(
                (
                    "[",
                    escape_for_character_class(element.start),
                    "-",
                    escape_for_character_class(element.end),
                    "]",
                )
            )
        )

    def visit_character_class(self, element: CharacterClass) -> None:
        self.stream.write_text("[")

        for i, subelement in enumerate(element.elements):
            if i > 0:
                self.stream.mark_breakpoint()

            if isinstance(subelement, Range):
                self.stream.write_text(
                    "".join(
                        (
                            escape_for_character_class(subelement.start),
                            "-",
                            escape_for_character_class(subelement.end),
                        )
                    )
                )
            elif isinstance(subelement, Literal):
                self.stream.write_text(escape_for_character_class(subelement.value))
            else:
                raise NotImplementedError(
                    f"sub-element {subelement} in element {element}"
                )

        self.stream.write_text("]")

    def visit_reference(self, element: Reference) -> None:
        self.stream.write_reference(element.name)


@ensure(lambda result: not (result[0] == "'") or result[-1] == "'")
@ensure(lambda result: not (result[0] == '"') or result[-1] == '"')
@ensure(lambda result: len(result) > 0)
def _tokens_to_str_literal(tokens: List[_Token]) -> str:
    """Concatenate the tokens and return a Python string literal."""
    has_reference = any(token.kind == _TokenKind.REFERENCE for token in tokens)

    if not has_reference:
        str_literal = repr("".join(token.value for token in tokens))
    else:
        regexp_writer = io.StringIO()
        for token in tokens:
            if token.kind == _TokenKind.TEXT:
                regexp_writer.write(token.value.replace("{", "{{").replace("}", "}}"))
            elif token.kind == _TokenKind.REFERENCE:
                regexp_writer.write("{")
                regexp_writer.write(token.value)
                regexp_writer.write("}")
            elif token.kind == _TokenKind.BREAK_POINT:
                pass
            else:
                raise NotImplementedError(token.kind)

        str_literal = f"f{repr(regexp_writer.getvalue())}"

    return str_literal


class _Segment:
    """Represent a list of tokens which should not be broken in the middle."""

    def __init__(self, tokens: Sequence[_Token]) -> None:
        self.tokens = tokens
        self.length = sum(len(token.value) for token in tokens)


# fmt: off
@require(lambda line_width: line_width > 0)
@ensure(
    lambda segments, result:
    all(
        segment == other_segment
        for segment, other_segment in zip(
            segments, (seg
                       for line in result
                       for seg in line))
    )
)
@ensure(
    lambda segments, result:
    len(segments) == sum(len(line) for line in result))
# fmt: on
def _wrap_segments(segments: List[_Segment], line_width: int) -> List[List[_Segment]]:
    """Wrap ``segments`` into lines that all optimistically fit on ``line_width``."""
    lines = []  # type: List[List[_Segment]]

    accumulator = []  # type: List[_Segment]
    accumulator_length = 0

    for segment in segments:
        if accumulator_length + segment.length > line_width:
            if len(accumulator) > 0:
                lines.append(accumulator)
                accumulator = []
                accumulator_length = 0

        accumulator.append(segment)
        accumulator_length += segment.length

    if len(accumulator) > 0:
        lines.append(accumulator)

    return lines


# fmt: off
@require(
    lambda table:
    all(
        identifier.isidentifier()
        for identifier in table
    )
)
@ensure(lambda result: not result.startswith('\n'))
@ensure(lambda result: not result.endswith('\n'))
# fmt: on
def represent(table: "collections.OrderedDict[str, Element]") -> str:
    """Compile the rule table to a snippet of Python code."""
    writer = io.StringIO()

    for rule_i, (identifier, regexp) in enumerate(table.items()):
        if rule_i > 0:
            writer.write("\n")

        representer = _Representer()

        representer.visit(regexp)

        # Apply a very naive estimation of the total length. This is a very vague
        # estimate: we do not account for curly brackets in references nor do we count
        # escape characters in string representation. However, this usually does the job
        # decently well.
        estimated_length = (
            len(identifier)
            + 3
            + sum(len(token.value) for token in representer.stream.tokens)
        )

        if estimated_length <= 70:
            regexp_str_literal = _tokens_to_str_literal(
                tokens=representer.stream.tokens
            )
            writer.write(f"{identifier} = {regexp_str_literal}")
        else:
            writer.write(f"{identifier} = (\n")

            # Split the tokens into segments. The lines should not break in the
            # middle of the segment.
            segments = []  # type: List[_Segment]
            accumulator = []  # type: List[_Token]

            for token in representer.stream.tokens:
                if token.kind == _TokenKind.BREAK_POINT:
                    if len(accumulator) > 0:
                        segments.append(_Segment(accumulator))
                        accumulator = []

                else:
                    accumulator.append(token)

            if len(accumulator) > 0:
                segments.append(_Segment(accumulator))

            lines_of_segments = _wrap_segments(
                segments=segments,
                # 70: arbitrary line width, 4: indention, 3: " = "
                line_width=70 - 4 - len(identifier) - 3,
            )

            for line_i, line in enumerate(lines_of_segments):
                if line_i > 0:
                    writer.write("\n")

                writer.write(" " * 4)

                # fmt: off
                regexp_str_literal = _tokens_to_str_literal(
                    [
                        token
                        for segment in line
                        for token in segment.tokens
                    ]
                )
                # fmt: on

                writer.write(regexp_str_literal)

            writer.write("\n)")

    return writer.getvalue()
