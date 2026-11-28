import csv
import math

import pytest

from src.check_balance import (
    ARMS,
    COVARIATES,
    REVIEW_THRESHOLD,
    BalanceInputError,
    check_balance,
    format_summary,
    standardized_difference,
)

BASE = (
    ("2", "20", "0", "1", "0", "Phone", "Rural"),
    ("3", "40", "1", "0", "1", "Web", "Surburban"),
    ("4", "60", "1", "1", "0", "Multichannel", "Urban"),
)


def _write_profiles(path, changes=None):
    with path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source)
        writer.writerow(["spend", *COVARIATES, "segment", "visit", "conversion"])
        for arm in ARMS:
            for i, values in enumerate(BASE):
                row = dict(zip(COVARIATES, values, strict=True))
                row.update((changes or {}).get((arm, i), {}))
                writer.writerow(
                    ["OPAQUE,SPEND", *row.values(), arm, "OPAQUE_VISIT", "OPAQUE_BUY"]
                )


def test_identical_arm_distributions_are_balanced_and_preserve_bytes(tmp_path):
    path = tmp_path / "balanced.csv"
    _write_profiles(path)
    original = path.read_bytes()

    result = check_balance(path, expected_records=9)

    assert result.status == "PASS"
    assert result.arm_sizes == dict.fromkeys(ARMS, 3)
    assert set(name for name, _ in result.diagnostics) == set(COVARIATES)
    assert all(
        smd.value == 0
        for contrasts in result.diagnostics.values()
        for smd in contrasts
    )
    assert path.read_bytes() == original
    output = format_summary(result)
    assert "Balance records: 9" in output
    for hidden in ("spend", "visit", "conversion", "OPAQUE", "history_segment"):
        assert hidden not in output


def test_imbalanced_numeric_and_categorical_pairs_are_flagged(tmp_path):
    path = tmp_path / "imbalanced.csv"
    _write_profiles(
        path,
        {
            ("Mens E-Mail", i): {"recency": str(5 + i), "channel": "Web"}
            for i in range(3)
        },
    )

    result = check_balance(path, expected_records=9)

    assert result.status == "REVIEW"
    numeric = result.diagnostics["recency", None]
    web = result.diagnostics["channel", "Web"]
    assert [smd.value for smd in numeric] == pytest.approx([3, 0, -3])
    assert [smd.value for smd in web] == pytest.approx([2, 0, -2])
    assert [smd.flagged for smd in numeric] == [True, False, True]
    assert [smd.flagged for smd in web] == [True, False, True]
    output = format_summary(result)
    assert "channel | Web | 3/3 (1.00000000) | 1/3 (0.33333333)" in output


@pytest.mark.parametrize(
    ("difference", "flagged"),
    [
        (REVIEW_THRESHOLD, False),
        (-REVIEW_THRESHOLD, False),
        (math.nextafter(REVIEW_THRESHOLD, 1), True),
        (math.nextafter(-REVIEW_THRESHOLD, -1), True),
    ],
)
def test_threshold_applies_to_unrounded_absolute_smd(difference, flagged):
    diagnostic = standardized_difference((difference, 1), (0, 1))

    assert diagnostic.value == difference
    assert diagnostic.flagged is flagged


def test_missing_invalid_and_zero_variance_have_explicit_denominators(tmp_path):
    path = tmp_path / "exceptions.csv"
    changes = {
        (arm, i): {"recency": "2"} for arm in ARMS for i in range(3)
    }
    for i in range(3):
        changes["No E-Mail", i]["history"] = ""
        changes["Womens E-Mail", i]["channel"] = "  "
    changes["Mens E-Mail", 1]["channel"] = "PRIVATE_INVALID_CATEGORY"
    _write_profiles(path, changes)

    result = check_balance(path, expected_records=9)

    assert result.status == "REVIEW"
    assert sum(result.arm_sizes.values()) == 9
    history = result.fields["No E-Mail", "history"]
    channel = result.fields["Mens E-Mail", "channel"]
    assert (history.valid, history.missing, history.invalid) == (0, 3, 0)
    assert (channel.valid, channel.missing, channel.invalid) == (2, 0, 1)
    assert channel.levels == {"Phone": 1, "Multichannel": 1}
    assert result.diagnostics["history", None][0].reason == "insufficient valid records"
    assert result.diagnostics["recency", None][0].reason == "zero pooled variance"
    phone = result.diagnostics["channel", "Phone"][1]
    assert phone.reason == "insufficient valid records"
    output = format_summary(result)
    assert "history | No E-Mail | 3 | 0 | 3 | 0" in output
    assert "channel | Phone | 1/2 (0.50000000)" in output
    assert "0/0 (UNDEFINED)" in output
    assert "PRIVATE_INVALID_CATEGORY" not in output


def test_constant_category_and_single_numeric_observation_are_undefined(tmp_path):
    path = tmp_path / "single.csv"
    path.write_text(
        ",".join(("segment", *COVARIATES))
        + "\n"
        + "\n".join(",".join((arm, *BASE[0])) for arm in ARMS),
        encoding="utf-8",
    )

    result = check_balance(path, expected_records=3)

    assert result.diagnostics["history", None][0].reason == "insufficient valid records"
    assert result.diagnostics["channel", "Phone"][0].reason == "zero pooled variance"


def test_bad_assignment_aborts_without_echoing_its_value(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text(
        ",".join(("segment", *COVARIATES))
        + "\n"
        + ",".join(("PRIVATE_LABEL", *BASE[0])),
        encoding="utf-8",
    )

    with pytest.raises(
        BalanceInputError, match=r"^Invalid assignment at data record 1\.$"
    ):
        check_balance(path, expected_records=1)
