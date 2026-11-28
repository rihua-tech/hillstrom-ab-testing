"""Run the Hillstrom assignment-only SRM check after the documented input gates."""

import argparse
import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from scipy.stats import chisquare

from .audit_data_quality import CATEGORIES
from .validate_schema import EXPECTED_RECORDS

ARMS = tuple(sorted(CATEGORIES["segment"]))
HOLD_THRESHOLD = 0.001


class SRMInputError(ValueError):
    """An input problem that prevents an SRM test."""


@dataclass(frozen=True)
class SRMResult:
    counts: tuple[int, ...]
    expected_per_arm: float
    statistic: float
    p_value: float

    @property
    def degrees_of_freedom(self) -> int:
        return len(self.counts) - 1

    @property
    def hold(self) -> bool:
        return self.p_value < HOLD_THRESHOLD


def count_assignments(
    path: Path, *, expected_records: int = EXPECTED_RECORDS
) -> tuple[int, ...]:
    """Use only the segment cell in each CSV data record."""
    counts = dict.fromkeys(ARMS, 0)
    try:
        with path.open(encoding="utf-8", newline="") as source:
            reader = csv.reader(source, strict=True)
            header = next(reader, [])
            if header.count("segment") != 1:
                raise SRMInputError("CSV must contain exactly one segment column.")
            index = header.index("segment")
            for number, row in enumerate(reader, 1):
                if len(row) != len(header):
                    raise SRMInputError(f"Wrong CSV width at data record {number}.")
                segment = row[index]
                if not segment.strip():
                    raise SRMInputError(f"Missing segment at data record {number}.")
                if segment not in counts:
                    raise SRMInputError(
                        f"Illegal segment label at data record {number}."
                    )
                counts[segment] += 1
    except (OSError, UnicodeDecodeError, csv.Error):
        raise SRMInputError("Could not read complete CSV records.") from None

    observed_records = sum(counts.values())
    if observed_records != expected_records:
        raise SRMInputError(
            f"Expected {expected_records} assignments, counted {observed_records}."
        )
    return tuple(counts.values())


def pearson_srm(counts: Sequence[int]) -> SRMResult:
    """Test the frozen 1:1:1 allocation with no fitted parameters."""
    if len(counts) != len(ARMS) or any(count < 0 for count in counts):
        raise SRMInputError("Three nonnegative assignment counts are required.")
    total = sum(counts)
    if total == 0:
        raise SRMInputError("No assignments to test.")
    expected = total / len(ARMS)
    test = chisquare(counts, f_exp=[expected] * len(ARMS))
    return SRMResult(tuple(counts), expected, float(test.statistic), float(test.pvalue))


def format_summary(result: SRMResult) -> str:
    total = sum(result.counts)
    lines = [
        f"Assignments counted: {total}",
        "Assignment | Observed count | Observed proportion | Expected count (N/3)",
    ]
    for arm, count in zip(ARMS, result.counts, strict=True):
        lines.append(f"{arm} | {count} | {count / total} | {result.expected_per_arm}")
    lines.extend(
        [
            f"Pearson chi-square: {result.statistic}",
            f"Degrees of freedom: {result.degrees_of_freedom}",
            f"p-value: {result.p_value}",
            f"HOLD threshold: p < {HOLD_THRESHOLD}",
            f"SRM status: {'HOLD' if result.hold else 'PASS'}",
        ]
    )
    if result.hold:
        lines.append("Confirmatory interpretation: HOLD pending investigation")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="path to the gated Hillstrom CSV")
    args = parser.parse_args(argv)
    try:
        result = pearson_srm(count_assignments(args.path))
    except SRMInputError as error:
        print(f"SRM status: NOT RUN. {error}")
        return 1
    print(format_summary(result))
    return 2 if result.hold else 0


if __name__ == "__main__":
    raise SystemExit(main())
