# pylint: disable=missing-docstring

import unittest

import abnf_to_regexp.abnf_transformation


class TestLetterRanges(unittest.TestCase):
    def test_zero_character(self) -> None:
        self.assertFalse(
            abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                start_ord=0, end_ord=0
            )
        )

    def test_after_last_range(self) -> None:
        last_end = abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGE_ENDS[-1]

        self.assertFalse(
            abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                start_ord=last_end + 1, end_ord=last_end + 1
            )
        )

    def test_whole_gamuth(self) -> None:
        first_start = abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGE_STARTS[0]
        last_end = abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGE_ENDS[-1]

        self.assertTrue(
            abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                start_ord=first_start, end_ord=last_end
            )
        )

    def test_wider_than_gamuth(self) -> None:
        first_start = abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGE_STARTS[0]
        last_end = abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGE_ENDS[-1]

        self.assertTrue(
            abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                start_ord=first_start - 1, end_ord=last_end + 1
            )
        )

    def test_misses_between_ranges(self) -> None:
        for (_, end1), (start2, _) in (
                abnf_to_regexp.abnf_transformation.pairwise(
                    abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGES
                )
        ):
            if start2 - end1 <= 2:
                continue

            self.assertFalse(
                abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                    start_ord=end1 + 1, end_ord=start2 - 1
                )
            )

    def test_hits_with_start_and_end_between_ranges(self) -> None:
        for (start1, end1), (start2, end2) in (
                abnf_to_regexp.abnf_transformation.pairwise(
                    abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGES
                )
        ):
            self.assertTrue(
                abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                    start_ord=min(start1 + 1, end1),
                    end_ord=min(start2 + 1, end2)
                )
            )

    def test_hit_with_point_ranges(self) -> None:
        for start, end in abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGES:
            self.assertTrue(
                abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                    start_ord=start,
                    end_ord=start
                )
            )

            self.assertTrue(
                abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                    start_ord=end,
                    end_ord=end
                )
            )

    def test_misses_between_ranges_with_point_range(self) -> None:
        for (_, end1), (start2, _) in (
                abnf_to_regexp.abnf_transformation.pairwise(
                    abnf_to_regexp.abnf_transformation._LETTER_ORD_RANGES
                )
        ):
            if start2 - end1 <= 1:
                continue

            self.assertFalse(
                abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                    start_ord=end1 + 1, end_ord=end1 + 1
                )
            )

    def test_with_explicit_case(self) -> None:
        self.assertTrue(
            abnf_to_regexp.abnf_transformation._range_overlaps_with_a_letter_range(
                start_ord=ord('b'),
                end_ord=ord('d')
            )
        )


if __name__ == "__main__":
    unittest.main()
