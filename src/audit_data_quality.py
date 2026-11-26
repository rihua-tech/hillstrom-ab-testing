"""Audit Hillstrom field quality and report pooled, count-only diagnostics."""

import argparse
import csv
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .validate_schema import EXPECTED_FIELDS, EXPECTED_RECORDS, validate_csv

# Raw labels are described in the Phase 1.3 contract in data/README.md.
HISTORY_BANDS: dict[str, tuple[int, int | None]] = {
    "1) $0 - $100": (0, 100),
    "2) $100 - $200": (100, 200),
    "3) $200 - $350": (200, 350),
    "4) $350 - $500": (350, 500),
    "5) $500 - $750": (500, 750),
    "6) $750 - $1,000": (750, 1000),
    "7) $1,000 +": (1000, None),
}
CATEGORIES = {
    "history_segment": frozenset(HISTORY_BANDS),
    "zip_code": frozenset({"Rural", "Surburban", "Urban"}),
    "channel": frozenset({"Phone", "Web", "Multichannel"}),
    "segment": frozenset({"No E-Mail", "Mens E-Mail", "Womens E-Mail"}),
}
BINARY_FIELDS = frozenset({"mens", "womens", "newbie", "visit", "conversion"})
PRE_TREATMENT_FIELDS = (
    "recency",
    "history_segment",
    "history",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
)
HOLD_FIELDS = ("conversion", "segment")
CONSISTENCY_RULES = (
    "history_outside_documented_band",
    "positive_spend_with_no_purchase",
)


class AuditInputError(ValueError):
    """A safe diagnostic for input that could not be audited."""


@dataclass(frozen=True)
class AuditResult:
    records: int
    field_issues: dict[str, Counter[str]]
    consistency: Counter[str]
    duplicate_groups: int
    duplicate_records: int
    duplicate_excess_records: int

    @property
    def hold_fields(self) -> tuple[str, ...]:
        return tuple(name for name in HOLD_FIELDS if self.field_issues[name])

    @property
    def status(self) -> str:
        if self.hold_fields:
            return "HOLD"
        if any(self.field_issues.values()) or self.consistency or self.duplicate_groups:
            return "REVIEW"
        return "PASS"


def _check_field(name: str, raw: str) -> tuple[str | None, Decimal | None]:
    if not raw.strip():
        return "missing", None

    if name in CATEGORIES:
        return (None if raw in CATEGORIES[name] else "illegal_category"), None

    try:
        number = Decimal(raw)
    except InvalidOperation:
        return "not_numeric", None

    if not number.is_finite():
        return "non_finite", None
    if name in BINARY_FIELDS and number not in (0, 1):
        return "non_binary", None
    if name in {"recency", "history", "spend"} and number < 0:
        return "negative", None
    if name == "recency":
        if number != number.to_integral_value():
            return "not_integer", None
        if number > 12:
            return "outside_12_month_window", None
    return None, number


def _audit_rows(rows: Iterable[dict[str, str]]) -> AuditResult:
    issues: dict[str, Counter[str]] = {name: Counter() for name in EXPECTED_FIELDS}
    consistency: Counter[str] = Counter()
    pre_treatment_keys: Counter[tuple[str, ...]] = Counter()
    records = 0

    for row in rows:
        records += 1
        numbers = {}
        for name in EXPECTED_FIELDS:
            issue, number = _check_field(name, row[name])
            if issue is not None:
                issues[name][issue] += 1
            elif number is not None:
                numbers[name] = number

        history = numbers.get("history")
        band = HISTORY_BANDS.get(row["history_segment"])
        if history is not None and band is not None:
            low, high = band
            if history < low or (high is not None and history > high):
                consistency["history_outside_documented_band"] += 1

        spend = numbers.get("spend")
        if numbers.get("conversion") == 0 and spend is not None and spend > 0:
            consistency["positive_spend_with_no_purchase"] += 1

        pre_treatment_keys[tuple(row[name] for name in PRE_TREATMENT_FIELDS)] += 1

    repeated = [size for size in pre_treatment_keys.values() if size > 1]
    return AuditResult(
        records=records,
        field_issues=issues,
        consistency=consistency,
        duplicate_groups=len(repeated),
        duplicate_records=sum(repeated),
        duplicate_excess_records=sum(repeated) - len(repeated),
    )


def audit_csv(path: Path, *, expected_records: int = EXPECTED_RECORDS) -> AuditResult:
    """Require the Phase 1.2 structure gate, then audit the file read-only."""
    validation = validate_csv(path, expected_records=expected_records)
    if not validation.passed:
        raise AuditInputError("Schema gate failed. " + " ".join(validation.errors))

    try:
        with path.open(encoding="utf-8", newline="") as source:
            reader = csv.reader(source, strict=True)
            header = next(reader, ())
            if Counter(header) != Counter(EXPECTED_FIELDS):
                raise AuditInputError("Header changed after the schema gate.")
            rows = (dict(zip(header, cells, strict=True)) for cells in reader)
            result = _audit_rows(rows)
    except AuditInputError:
        raise
    except (OSError, csv.Error, ValueError):
        raise AuditInputError(
            "Could not read complete CSV records during audit."
        ) from None

    if result.records != validation.record_count:
        raise AuditInputError("Record count changed after the schema gate.")
    return result


def format_summary(result: AuditResult) -> str:
    """Render only fixed labels, quality counts and gate status."""
    lines = [
        f"Records audited: {result.records}",
        "Field | Missing | Invalid | Invalid reasons (counts)",
    ]
    for name in EXPECTED_FIELDS:
        counts = result.field_issues[name]
        missing = counts["missing"]
        invalid = counts.total() - missing
        reasons = ", ".join(
            f"{reason}={count}"
            for reason, count in sorted(counts.items())
            if reason != "missing"
        )
        lines.append(f"{name} | {missing} | {invalid} | {reasons or '-'}")

    lines.append("Pooled consistency rule | Severity | Flagged records")
    lines.extend(
        f"{key} | REVIEW | {result.consistency[key]}" for key in CONSISTENCY_RULES
    )
    lines.extend(
        [
            f"Duplicate-looking pre-treatment groups: {result.duplicate_groups}",
            f"Records in those groups: {result.duplicate_records}",
            f"Extra records beyond one per group: {result.duplicate_excess_records}",
            "Customer uniqueness: unverified (no unique customer ID)",
            f"Audit status: {result.status}",
        ]
    )
    if result.hold_fields:
        fields = ", ".join(result.hold_fields)
        lines.append(f"Confirmatory inference: PAUSED ({fields})")
    else:
        lines.append("Confirmatory inference: no hold from this audit")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="path to the local Hillstrom CSV")
    args = parser.parse_args(argv)
    try:
        result = audit_csv(args.path)
    except AuditInputError as error:
        print(f"Audit status: NOT RUN. {error}")
        return 1

    print(format_summary(result))
    return 2 if result.hold_fields else 0


if __name__ == "__main__":
    raise SystemExit(main())
