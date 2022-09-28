"""Convert ABNF grammars to Python regular expressions."""

import argparse
import enum
import pathlib
import sys
from typing import Optional, TextIO

import abnf

import abnf_to_regexp
import abnf_to_regexp.single_regexp
import abnf_to_regexp.nested_python

assert __doc__ == abnf_to_regexp.__doc__


class Format(enum.Enum):
    """Represent the desired output format."""

    SINGLE_REGEXP = "single-regexp"
    PYTHON_NESTED = "python-nested"


def _assert_format_values_are_unique() -> None:
    """Check that the format values are unique and raise otherwise."""
    values = [entry.value for entry in Format]
    if len(values) != len(set(values)):
        raise AssertionError(f"Format values must be unique, but got: {values}")


_assert_format_values_are_unique()

FORMAT_FROM_STR = {entry.value: entry for entry in Format}


class Params:
    """Represent program parameters."""

    def __init__(
        self, input_path: pathlib.Path, output_path: Optional[pathlib.Path], fmt: Format
    ) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.fmt = fmt


def run(
    params: Params,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Execute the main routine."""
    pass  # for pydocstyle

    class OurRule(abnf.Rule):
        """Represent our ABNF rule list read from a file."""

        pass

    # We in-line abnf.parser.Rule.from_file and adapt it to be more robust to different
    # line endings.

    text = params.input_path.read_text(encoding="utf-8")

    # Enforce CRLF line endings
    text = text.replace("\r", "")

    if not text.endswith("\n"):
        text = text + "\n"

    text = text.replace("\n", "\r\n")

    try:
        node = abnf.parser.ABNFGrammarRule("rulelist").parse_all(text)
        visitor = abnf.parser.ABNFGrammarNodeVisitor(rule_cls=OurRule)
        visitor.visit(node)
    except abnf.ParseError as err:
        text = params.input_path.read_text()
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

    for rule in OurRule.rules():  # type: ignore
        if not hasattr(rule, "definition"):
            stderr.write(f"Unexpected rule without a definition: {rule.name!r}")
            return 1

    if params.fmt == Format.SINGLE_REGEXP:
        regexp = abnf_to_regexp.single_regexp.translate(rule_cls=OurRule)
        representation = abnf_to_regexp.single_regexp.represent(regexp)

    elif params.fmt == Format.PYTHON_NESTED:
        table, error = abnf_to_regexp.nested_python.translate(rule_cls=OurRule)
        if error:
            stderr.write(error + "\n")
            return 1

        assert table is not None

        representation = abnf_to_regexp.nested_python.represent(table=table)
    else:
        raise NotImplementedError(f"Unhandled format: {params.fmt}")

    representation_nl = representation + "\n"
    if params.output_path is None:
        stdout.write(representation_nl)
    else:
        params.output_path.write_text(representation_nl, encoding="utf-8")

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
    parser.add_argument(
        "--format",
        help="Output format; for example a single regular expression or a code snippet",
        choices=[entry.value for entry in Format],
        default=Format.SINGLE_REGEXP,
    )
    args = parser.parse_args()

    input_pth = pathlib.Path(args.input)
    output_pth = pathlib.Path(args.output) if args.output else None

    fmt = FORMAT_FROM_STR[args.format]

    params = Params(input_path=input_pth, output_path=output_pth, fmt=fmt)

    return run(
        params=params,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    sys.exit(main())
