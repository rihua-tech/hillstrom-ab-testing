"""Inspect the frozen pre-treatment covariates after the Phase 1.4 SRM gate."""

import argparse
import csv
import math
import statistics
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .audit_data_quality import CATEGORIES, _check_field
from .check_srm import ARMS
from .validate_schema import EXPECTED_RECORDS

NUMERIC = ("recency", "history")
BINARY = ("mens", "womens", "newbie")
LEVELS = {name: ("0", "1") for name in BINARY} | {
    name: tuple(sorted(CATEGORIES[name])) for name in ("channel", "zip_code")
}
COVARIATES = NUMERIC + tuple(LEVELS)
CONTRASTS = (
    ("Mens E-Mail", "No E-Mail"),
    ("Womens E-Mail", "No E-Mail"),
    ("Womens E-Mail", "Mens E-Mail"),
)
REVIEW_THRESHOLD = 0.10


class BalanceInputError(ValueError):
    """A safe diagnostic for input that could not be checked."""


@dataclass(frozen=True)
class FieldSummary:
    valid: int
    missing: int
    invalid: int
    mean: float | None = None
    sd: float | None = None
    levels: dict[str, int] = field(default_factory=dict)

    def moments(self, level: str | None) -> tuple[float, float] | None:
        if level is None:
            if self.mean is None or self.sd is None:
                return None
            return self.mean, self.sd
        if not self.valid:
            return None
        proportion = self.levels.get(level, 0) / self.valid
        return proportion, math.sqrt(proportion * (1 - proportion))


@dataclass(frozen=True)
class SMD:
    value: float | None
    reason: str | None = None

    @property
    def flagged(self) -> bool:
        return self.value is not None and abs(self.value) > REVIEW_THRESHOLD


@dataclass(frozen=True)
class BalanceResult:
    arm_sizes: dict[str, int]
    fields: dict[tuple[str, str], FieldSummary]
    diagnostics: dict[tuple[str, str | None], tuple[SMD, ...]]

    @property
    def status(self) -> str:
        if any(cell.missing or cell.invalid for cell in self.fields.values()):
            return "REVIEW"
        if any(
            smd.flagged or smd.value is None
            for contrasts in self.diagnostics.values()
            for smd in contrasts
        ):
            return "REVIEW"
        return "PASS"


@dataclass
class _FieldValues:
    numbers: list[float] = field(default_factory=list)
    levels: Counter[str] = field(default_factory=Counter)
    missing: int = 0
    invalid: int = 0

    def add(self, name: str, raw: str) -> None:
        issue, number = _check_field(name, raw)
        if issue == "missing":
            self.missing += 1
        elif issue is not None:
            self.invalid += 1
        elif number is None:
            self.levels[raw] += 1
        elif name in BINARY:
            self.levels[str(int(number))] += 1
        else:
            numeric = float(number)
            if math.isfinite(numeric):
                self.numbers.append(numeric)
            else:
                self.invalid += 1

    def summarize(self) -> FieldSummary:
        return FieldSummary(
            valid=len(self.numbers) + self.levels.total(),
            missing=self.missing,
            invalid=self.invalid,
            mean=statistics.mean(self.numbers) if self.numbers else None,
            sd=statistics.stdev(self.numbers) if len(self.numbers) >= 2 else None,
            levels=dict(self.levels),
        )


def standardized_difference(
    left: tuple[float, float] | None, right: tuple[float, float] | None
) -> SMD:
    """Use the unweighted root mean of the two variances as the denominator."""
    if left is None or right is None:
        return SMD(None, "insufficient valid records")
    left_mean, left_sd = left
    right_mean, right_sd = right
    scale = max(left_sd, right_sd)
    if scale == 0:
        return SMD(None, "zero pooled variance")
    ratio = min(left_sd, right_sd) / scale
    denominator = scale * math.sqrt((1 + ratio * ratio) / 2)
    value = (left_mean - right_mean) / denominator
    return SMD(value) if math.isfinite(value) else SMD(None, "non-finite SMD")


def check_balance(
    path: Path, *, expected_records: int = EXPECTED_RECORDS
) -> BalanceResult:
    """Read only the assignment and frozen balance fields from a gated CSV."""
    arm_sizes = dict.fromkeys(ARMS, 0)
    cells = {(arm, name): _FieldValues() for arm in ARMS for name in COVARIATES}
    try:
        with path.open(encoding="utf-8", newline="") as source:
            rows = csv.reader(source, strict=True)
            header = next(rows, [])
            required = ("segment", *COVARIATES)
            if any(header.count(name) != 1 for name in required):
                raise BalanceInputError("Required balance columns must occur once.")
            segment_index = header.index("segment")
            columns = tuple((name, header.index(name)) for name in COVARIATES)
            for number, row in enumerate(rows, 1):
                if len(row) != len(header):
                    raise BalanceInputError(f"Wrong CSV width at data record {number}.")
                arm = row[segment_index]
                if arm not in arm_sizes:
                    raise BalanceInputError(
                        f"Invalid assignment at data record {number}."
                    )
                arm_sizes[arm] += 1
                for name, index in columns:
                    cells[arm, name].add(name, row[index])
    except (OSError, UnicodeDecodeError, csv.Error):
        raise BalanceInputError("Could not read complete CSV records.") from None

    total = sum(arm_sizes.values())
    if total != expected_records:
        raise BalanceInputError(
            f"Expected {expected_records} records, counted {total}."
        )

    summaries = {key: cell.summarize() for key, cell in cells.items()}
    diagnostics = {
        (name, level): tuple(
            standardized_difference(
                summaries[left, name].moments(level),
                summaries[right, name].moments(level),
            )
            for left, right in CONTRASTS
        )
        for name in COVARIATES
        for level in LEVELS.get(name, (None,))
    }
    return BalanceResult(arm_sizes, summaries, diagnostics)


def _format_smd(smd: SMD) -> str:
    if smd.value is None:
        return f"UNDEFINED ({smd.reason})"
    suffix = " REVIEW" if smd.flagged else ""
    return f"{smd.value:+.8f}{suffix}"


def format_summary(result: BalanceResult) -> str:
    lines = [
        f"Balance records: {sum(result.arm_sizes.values())}",
        "Field | Assignment | Arm N | Valid n | Missing | Invalid",
    ]
    for name in COVARIATES:
        for arm, total in result.arm_sizes.items():
            cell = result.fields[arm, name]
            lines.append(
                f"{name} | {arm} | {total} | {cell.valid} | "
                f"{cell.missing} | {cell.invalid}"
            )

    lines.append("Field | Level | " + " | ".join(result.arm_sizes))
    for name, levels in LEVELS.items():
        for level in levels:
            cells = []
            for arm in result.arm_sizes:
                cell = result.fields[arm, name]
                count = cell.levels.get(level, 0)
                share = f"{count / cell.valid:.8f}" if cell.valid else "UNDEFINED"
                cells.append(f"{count}/{cell.valid} ({share})")
            lines.append(f"{name} | {level} | " + " | ".join(cells))

    lines.append("SMD | Men's - Control | Women's - Control | Women's - Men's")
    for (name, level), contrasts in result.diagnostics.items():
        label = name if level is None else f"{name}={level}"
        lines.append(f"{label} | " + " | ".join(map(_format_smd, contrasts)))
    lines.append(f"Balance review threshold: |SMD| > {REVIEW_THRESHOLD:.2f}")
    lines.append(f"Balance status: {result.status}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="path to the gated Hillstrom CSV")
    args = parser.parse_args(argv)
    try:
        result = check_balance(args.path)
    except BalanceInputError as error:
        print(f"Balance status: NOT RUN. {error}")
        return 1
    print(format_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
