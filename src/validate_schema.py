"""Validate Hillstrom CSV structure without examining or reporting field values."""

import argparse
import csv
import re
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

# Frozen plan-v1.1 §2 and the scikit-uplift v0.3.1 field dictionary.
EXPECTED_FIELDS = (
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
    "segment",
    "visit",
    "conversion",
    "spend",
)
EXPECTED_RECORDS = 64_000

# csv.reader(strict=True) still accepts literal quotes in unquoted fields.
# Check quoting on the original lines grouped into a record by the CSV reader.
_FIELD = r'(?:"(?:[^"]|"")*"|[^",\r\n]*)'
_RECORD = re.compile(rf"{_FIELD}(?:,{_FIELD})*(?:\r\n|\r|\n)?")


@dataclass(frozen=True)
class ValidationResult:
    record_count: int | None
    errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.errors


def _header_errors(header: list[str], expected_fields: Sequence[str]) -> list[str]:
    counts = Counter(header)
    expected = set(expected_fields)
    missing = [field for field in expected_fields if field not in counts]
    unexpected = [str(i) for i, field in enumerate(header, 1) if field not in expected]
    duplicates = [str(i) for i, field in enumerate(header, 1) if counts[field] > 1]
    errors = []
    if missing:
        errors.append(f"Missing header fields: {', '.join(missing)}.")
    if unexpected:
        errors.append(f"Unexpected header field positions: {', '.join(unexpected)}.")
    if duplicates:
        errors.append(f"Duplicate header field positions: {', '.join(duplicates)}.")
    return errors


def _track_lines(lines: Iterable[str], record_lines: list[str]) -> Iterator[str]:
    for line in lines:
        record_lines.append(line)
        yield line


def validate_csv(
    path: Path,
    *,
    expected_fields: Sequence[str] = EXPECTED_FIELDS,
    expected_records: int = EXPECTED_RECORDS,
) -> ValidationResult:
    """Check the header, CSV syntax, record widths, and complete record count."""
    errors: list[str] = []
    record_count: int | None = 0
    expected_width = len(expected_fields)
    header_seen = False
    wrong_width_count = 0
    first_wrong_width: tuple[int, int] | None = None

    try:
        with path.open(encoding="utf-8", newline="") as source:
            record_lines: list[str] = []
            reader = csv.reader(_track_lines(source, record_lines), strict=True)
            for number, fields in enumerate(reader):
                if _RECORD.fullmatch("".join(record_lines)) is None:
                    raise csv.Error
                record_lines.clear()
                if number == 0:
                    header_seen = True
                    errors.extend(_header_errors(fields, expected_fields))
                    continue
                record_count = number
                if len(fields) != expected_width:
                    wrong_width_count += 1
                    if first_wrong_width is None:
                        first_wrong_width = (number, len(fields))
    except csv.Error:
        record_count = None
        errors.append(f"Malformed CSV near physical line {reader.line_num}.")
    except UnicodeDecodeError:
        record_count = None
        errors.append("CSV could not be decoded as UTF-8.")
    except OSError:
        record_count = None
        errors.append("Could not read the specified CSV.")

    if first_wrong_width is not None:
        number, observed_width = first_wrong_width
        errors.append(
            f"Wrong-width data records: {wrong_width_count}. First at data record "
            f"{number}: expected {expected_width} fields, found {observed_width}."
        )
    if record_count is not None:
        if not header_seen:
            errors.append("CSV header is missing.")
        if record_count != expected_records:
            errors.append(
                f"Data record count mismatch: expected {expected_records}, "
                f"found {record_count}."
            )
    return ValidationResult(record_count, tuple(errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="path to the local Hillstrom CSV")
    args = parser.parse_args(argv)
    result = validate_csv(args.path)

    print(f"Expected fields ({len(EXPECTED_FIELDS)}): {', '.join(EXPECTED_FIELDS)}")
    print(f"Expected data records: {EXPECTED_RECORDS}")
    observed = (
        "unavailable (parsing incomplete)"
        if result.record_count is None
        else result.record_count
    )
    print(f"Observed data records: {observed}")
    for error in result.errors:
        print(f"ERROR: {error}")
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
