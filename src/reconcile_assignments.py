"""Independently count Hillstrom assignments with SQLite and compare to Python."""

import argparse
import csv
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .check_srm import ARMS, SRMInputError, count_assignments
from .validate_schema import EXPECTED_RECORDS, validate_csv

SQL_PATH = Path(__file__).resolve().parent.parent / "sql" / "reconcile_assignments.sql"


class ReconciliationInputError(ValueError):
    """A safe diagnostic for a reconciliation that could not run."""


@dataclass(frozen=True)
class SQLCounts:
    total: int
    by_arm: dict[str, int]
    missing: int
    illegal: int

    @property
    def accounted_for(self) -> int:
        return sum(self.by_arm.values()) + self.missing + self.illegal


@dataclass(frozen=True)
class Reconciliation:
    sql: SQLCounts
    python_total: int
    python_by_arm: dict[str, int] | None
    python_error: str | None = None

    @property
    def issues(self) -> tuple[str, ...]:
        issues = []
        if self.sql.total != self.python_total:
            issues.append("SQLite total differs from the Python schema count.")
        if self.sql.accounted_for != self.sql.total:
            issues.append("SQLite assignment categories do not sum to the full total.")
        if self.sql.missing or self.sql.illegal:
            issues.append("SQLite found missing or illegal assignment labels.")
        if self.python_by_arm is None:
            issues.append("Python SRM assignment counts are unavailable.")
        else:
            if sum(self.python_by_arm.values()) != self.python_total:
                issues.append("Python SRM counts do not sum to the schema total.")
            for arm in ARMS:
                if self.sql.by_arm[arm] != self.python_by_arm[arm]:
                    issues.append(f"SQLite and Python differ for {arm}.")
        return tuple(issues)


def _segments_for_sql(path: Path) -> Iterator[tuple[str]]:
    """Reopen the CSV and project each segment into one SQLite row."""
    with path.open(encoding="utf-8", newline="") as source:
        rows = csv.reader(source, strict=True)
        header = next(rows, [])
        if header.count("segment") != 1:
            raise ReconciliationInputError("CSV requires exactly one segment column.")
        index = header.index("segment")
        for number, row in enumerate(rows, 1):
            if len(row) != len(header):
                raise ReconciliationInputError(
                    f"Wrong CSV width at data record {number}."
                )
            yield (row[index],)


def count_in_sql(path: Path) -> SQLCounts:
    """Use SQL to count the independently loaded full assignment projection."""
    try:
        query = SQL_PATH.read_text(encoding="utf-8")
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute("CREATE TABLE assignments (segment TEXT NOT NULL)")
            connection.executemany(
                "INSERT INTO assignments (segment) VALUES (?)", _segments_for_sql(path)
            )
            total, control, mens, womens, missing, illegal = connection.execute(
                query
            ).fetchone()
    except (OSError, UnicodeDecodeError, csv.Error, sqlite3.Error):
        raise ReconciliationInputError(
            "SQLite could not complete the assignment import and query."
        ) from None
    return SQLCounts(
        total,
        {"No E-Mail": control, "Mens E-Mail": mens, "Womens E-Mail": womens},
        missing,
        illegal,
    )


def reconcile_csv(
    path: Path, *, expected_records: int = EXPECTED_RECORDS
) -> Reconciliation:
    validation = validate_csv(path, expected_records=expected_records)
    if not validation.passed or validation.record_count is None:
        raise ReconciliationInputError(
            "Schema gate failed. " + " ".join(validation.errors)
        )

    sql = count_in_sql(path)
    try:
        counts = count_assignments(path, expected_records=validation.record_count)
    except SRMInputError as error:
        return Reconciliation(sql, validation.record_count, None, str(error))
    by_arm = dict(zip(ARMS, counts, strict=True))
    return Reconciliation(sql, validation.record_count, by_arm)


def format_summary(result: Reconciliation) -> str:
    lines = ["Population | Python | SQLite | Difference (SQLite - Python)"]
    pairs: list[tuple[str, int | None, int]] = [
        ("Total", result.python_total, result.sql.total)
    ]
    pairs.extend(
        (
            arm,
            result.python_by_arm[arm] if result.python_by_arm is not None else None,
            result.sql.by_arm[arm],
        )
        for arm in ARMS
    )
    for label, python_count, sql_count in pairs:
        observed = python_count if python_count is not None else "unavailable"
        difference = sql_count - python_count if python_count is not None else "unknown"
        lines.append(f"{label} | {observed} | {sql_count} | {difference}")
    lines.extend(
        [
            f"SQLite missing assignments: {result.sql.missing}",
            f"SQLite illegal assignments: {result.sql.illegal}",
            f"SQLite assignments accounted for: {result.sql.accounted_for}",
        ]
    )
    if result.python_error:
        lines.append(f"Python SRM input: {result.python_error}")
    issues = result.issues
    lines.extend(f"ERROR: {issue}" for issue in issues)
    lines.append(f"SQL reconciliation status: {'BLOCKED' if issues else 'PASS'}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="path to the gated Hillstrom CSV")
    args = parser.parse_args(argv)
    try:
        result = reconcile_csv(args.path)
    except ReconciliationInputError as error:
        print(f"SQL reconciliation status: NOT RUN. {error}")
        return 1
    print(format_summary(result))
    return 2 if result.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
