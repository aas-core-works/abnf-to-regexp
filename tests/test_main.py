# pylint: disable=missing-docstring
# pylint: disable=no-self-use

import io
import os
import pathlib
import re
import unittest
from typing import Optional

import abnf_to_regexp.main


def represent_diff(expected_text: str, got_text: str) -> Optional[str]:
    """Generate a diff message with +-30 characters from the first difference."""
    width = max(len(expected_text), len(got_text))

    expected_padded = expected_text.ljust(width, '\0')
    got_padded = got_text.ljust(width, '\0')

    first_diff_index = -1
    for i, (expected, got) in enumerate(zip(expected_padded, got_padded)):
        if expected != got:
            first_diff_index = i
            break

    if first_diff_index == -1:
        return None

    result = io.StringIO()

    result.write('Offset: expected vs got\n')
    for i in range(max(0, first_diff_index - 30), min(width, first_diff_index + 30)):
        expected = repr(expected_text[i]) if i < len(expected_text) else 'N/A'
        got = repr(got_text[i]) if i < len(got_text) else 'N/A'

        result.write(f'{i + 1:4d}: {expected} vs {got}')

        if i == first_diff_index:
            result.write(" <<< first difference here <<<")

        result.write("\n")

    return result.getvalue()


class TestAgainstRecordings(unittest.TestCase):
    def test_single_regexp(self) -> None:
        this_dir = pathlib.Path(os.path.realpath(__file__)).parent
        data_dir = this_dir.parent / "test_data" / "single-regexp"

        for case_dir in sorted(data_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            grammar_pth = case_dir / "grammar.abnf"

            stdout = io.StringIO()
            stderr = io.StringIO()

            abnf_to_regexp.main.run(
                params=abnf_to_regexp.main.Params(
                    input_path=grammar_pth,
                    output_path=None,
                    fmt=abnf_to_regexp.main.Format.SINGLE_REGEXP
                ),
                stdout=stdout,
                stderr=stderr
            )

            expected_err_pth = case_dir / "expected.err"
            expected_out_pth = case_dir / "expected.out"

            # Set to True if you are debugging or updating the tests
            record = False

            if record:
                expected_err_pth.write_text(stderr.getvalue(), encoding='utf-8')
                expected_out_pth.write_text(stdout.getvalue(), encoding='utf-8')

            expected_err = expected_err_pth.read_text(encoding='utf-8')
            expected_out = expected_out_pth.read_text(encoding='utf-8')

            diff = represent_diff(expected_err, stderr.getvalue())
            if diff:
                raise AssertionError(
                    f"Expected and obtained STDERR differ on {case_dir}. "
                    f"Expected error:\n{expected_err!r}\n\n"
                    f"Got error:\n{stderr.getvalue()!r}\n\n"
                    f"The diff was:\n{diff}")

            diff = represent_diff(expected_out, stdout.getvalue())
            if diff:
                raise AssertionError(
                    f"Expected and obtained STDOUT differ on {case_dir}. "
                    f"The diff was:\n{diff}")

            if not stderr.getvalue():
                abnf_re_str = stdout.getvalue().strip()
                try:
                    abnf_re = re.compile(abnf_re_str)
                except re.error as err:
                    lines = abnf_re_str.splitlines()

                    if err.lineno is None or err.colno is None:
                        raise

                    line = lines[err.lineno - 1]

                    raise AssertionError(
                        f"Failed to compile the regular exception: {err}; "
                        f"relevant excerpt is (prefix, character, suffix):\n"
                        f"{line[err.colno - 30:err.colno - 1]}\n"
                        f"{line[err.colno - 1]}\n"
                        f"{line[err.colno:err.colno + 30]}\n"
                        f"The whole regular exception is:\n{abnf_re_str!r}")

                for example_pth in sorted(case_dir.glob("example*.txt")):
                    example = example_pth.read_text()
                    self.assertRegex(example, abnf_re)

                for counter_example_pth in sorted(
                        case_dir.glob("counter_example*.txt")):
                    counter_example = counter_example_pth.read_text()
                    self.assertIsNone(
                        abnf_re.match(counter_example),
                        f"Expected the counter-example not to match "
                        f"for {grammar_pth}: {counter_example_pth}")

    def test_python_nested(self) -> None:
        this_dir = pathlib.Path(os.path.realpath(__file__)).parent
        data_dir = this_dir.parent / "test_data" / "nested-python"

        for case_dir in sorted(data_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            grammar_pth = case_dir / "grammar.abnf"

            stdout = io.StringIO()
            stderr = io.StringIO()

            abnf_to_regexp.main.run(
                params=abnf_to_regexp.main.Params(
                    input_path=grammar_pth,
                    output_path=None,
                    fmt=abnf_to_regexp.main.Format.PYTHON_NESTED
                ),
                stdout=stdout,
                stderr=stderr
            )

            expected_err_pth = case_dir / "expected.err"
            expected_out_pth = case_dir / "expected.py"

            # Set to True if you are debugging or updating the tests
            record = False

            if record:
                expected_err_pth.write_text(stderr.getvalue(), encoding='utf-8')
                expected_out_pth.write_text(stdout.getvalue(), encoding='utf-8')

            expected_err = expected_err_pth.read_text(encoding='utf-8')
            expected_out = expected_out_pth.read_text(encoding='utf-8')

            diff = represent_diff(expected_err, stderr.getvalue())
            if diff:
                raise AssertionError(
                    f"Expected and obtained STDERR differ on {case_dir}. "
                    f"Expected error:\n{expected_err!r}\n\n"
                    f"Got error:\n{stderr.getvalue()!r}\n\n"
                    f"The diff was:\n{diff}")

            diff = represent_diff(expected_out, stdout.getvalue())
            if diff:
                raise AssertionError(
                    f"Expected and obtained STDOUT differ on {case_dir}. "
                    f"The diff was:\n{diff}")

            if not stderr.getvalue():
                code = stdout.getvalue().strip()
                try:
                    compile(code, "<abnf-to-regexp-test>", mode='exec')
                except Exception:
                    raise AssertionError(
                        f"Failed to compile code as in {expected_out_pth}:\n"
                        f"{code}"
                    )

if __name__ == "__main__":
    unittest.main()
