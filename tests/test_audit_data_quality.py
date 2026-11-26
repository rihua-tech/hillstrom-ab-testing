import csv

import pytest

from src import audit_data_quality
from src.audit_data_quality import audit_csv, format_summary
from src.validate_schema import EXPECTED_FIELDS

VALID = {
    "recency": "1",
    "history_segment": "1) $0 - $100",
    "history": "50",
    "mens": "0",
    "womens": "1",
    "zip_code": "Surburban",
    "newbie": "0",
    "channel": "Phone",
    "segment": "No E-Mail",
    "visit": "1",
    "conversion": "1",
    "spend": "15.20",
}


def _write_csv(tmp_path, *changes):
    path = tmp_path / "synthetic.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=EXPECTED_FIELDS[::-1])
        writer.writeheader()
        writer.writerows(VALID | overrides for overrides in changes)
    return path


def test_valid_audit_keeps_bytes_and_accepts_shared_history_boundary(tmp_path):
    path = _write_csv(
        tmp_path,
        {"history": "100", "visit": "0"},
        {"history": "100", "history_segment": "2) $100 - $200"},
    )
    original = path.read_bytes()

    result = audit_csv(path, expected_records=2)

    assert result.status == "PASS"
    assert result.records == 2
    assert not any(result.field_issues.values())
    assert not result.consistency
    assert path.read_bytes() == original


def test_missing_is_separate_from_invalid(tmp_path):
    path = _write_csv(
        tmp_path,
        {"conversion": "", "history": "   ", "visit": ""},
        {"conversion": "NA", "visit": "2", "spend": " "},
    )

    result = audit_csv(path, expected_records=2)

    assert result.field_issues["conversion"] == {"missing": 1, "not_numeric": 1}
    assert result.field_issues["visit"] == {"missing": 1, "non_binary": 1}
    assert result.field_issues["history"] == {"missing": 1}
    assert result.field_issues["spend"] == {"missing": 1}
    assert result.hold_fields == ("conversion",)
    assert "conversion | 1 | 1 | not_numeric=1" in format_summary(result)


def test_illegal_categories_numeric_types_binary_values_and_negatives(tmp_path):
    path = _write_csv(
        tmp_path,
        {
            "segment": "unexpected",
            "zip_code": "Suburban",
            "channel": "store",
            "history_segment": "wrong band",
            "recency": "1.25",
            "history": "bad history",
            "mens": "1.000000000000000001",
            "womens": "-1",
            "newbie": "2",
            "visit": "2",
            "conversion": "1.5",
            "spend": "-0.01",
        },
        {"recency": "13", "history": "-2"},
    )

    result = audit_csv(path, expected_records=2)

    for name in ("segment", "zip_code", "channel", "history_segment"):
        assert result.field_issues[name] == {"illegal_category": 1}
    for name in ("mens", "womens", "newbie", "visit", "conversion"):
        assert result.field_issues[name] == {"non_binary": 1}
    assert result.field_issues["recency"] == {
        "not_integer": 1,
        "outside_12_month_window": 1,
    }
    assert result.field_issues["history"] == {"not_numeric": 1, "negative": 1}
    assert result.field_issues["spend"] == {"negative": 1}
    assert result.hold_fields == ("conversion", "segment")
    assert not result.consistency


def test_non_finite_values_are_invalid_and_do_not_enter_consistency_checks(tmp_path):
    path = _write_csv(
        tmp_path,
        {
            "recency": "-Infinity",
            "history": "NaN",
            "visit": "nan",
            "conversion": "Infinity",
            "spend": "sNaN",
        },
    )

    result = audit_csv(path, expected_records=1)

    for name in ("recency", "history", "visit", "conversion", "spend"):
        assert result.field_issues[name] == {"non_finite": 1}
    assert result.hold_fields == ("conversion",)
    assert not result.consistency


def test_consistency_findings_require_valid_inputs_and_are_review_only(tmp_path):
    path = _write_csv(
        tmp_path,
        {"history": "101", "conversion": "0"},
        {"history": "900", "history_segment": "7) $1,000 +", "spend": "-1"},
        {"history": "", "conversion": "0", "spend": "NaN"},
    )

    result = audit_csv(path, expected_records=3)

    assert result.consistency == {
        "history_outside_documented_band": 2,
        "positive_spend_with_no_purchase": 1,
    }
    assert result.status == "REVIEW"
    assert not result.hold_fields
    assert "positive_spend_with_no_purchase | REVIEW | 1" in format_summary(result)


def test_duplicate_candidates_use_exact_pretreatment_fields_only(tmp_path):
    path = _write_csv(
        tmp_path,
        {},
        {"segment": "Mens E-Mail", "visit": "0", "conversion": "0", "spend": "0"},
        {"segment": "Womens E-Mail", "spend": "34.00"},
        {"history": "50.0"},
        {"recency": "2"},
        {"recency": "2", "spend": "10"},
    )

    result = audit_csv(path, expected_records=6)

    assert result.records == 6
    assert (result.duplicate_groups, result.duplicate_records) == (2, 5)
    assert result.duplicate_excess_records == 3
    assert result.status == "REVIEW"


@pytest.mark.parametrize(
    ("name", "value"),
    [("conversion", ""), ("conversion", "3"), ("segment", ""), ("segment", "bad")],
)
def test_each_gate_field_holds_when_missing_or_invalid(tmp_path, name, value):
    path = _write_csv(tmp_path, {name: value})

    result = audit_csv(path, expected_records=1)

    assert result.status == "HOLD"
    assert result.hold_fields == (name,)
    assert f"Confirmatory inference: PAUSED ({name})" in format_summary(result)


def test_cli_prints_only_quality_counts_and_hold_status(tmp_path, monkeypatch, capsys):
    path = _write_csv(
        tmp_path,
        {"segment": "RAW_ASSIGNMENT_MARKER", "conversion": "RAW_OUTCOME_MARKER"},
        {"segment": "Mens E-Mail", "spend": "4321.98765"},
    )
    monkeypatch.setattr(
        audit_data_quality,
        "audit_csv",
        lambda path: audit_csv(path, expected_records=2),
    )

    assert audit_data_quality.main([str(path)]) == 2

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Records audited: 2" in captured.out
    assert "conversion | 0 | 1 | not_numeric=1" in captured.out
    assert "spend | 0 | 0 | -" in captured.out
    assert "Confirmatory inference: PAUSED (conversion, segment)" in captured.out
    for raw in (
        "RAW_ASSIGNMENT_MARKER",
        "RAW_OUTCOME_MARKER",
        "Mens E-Mail",
        "4321.98765",
    ):
        assert raw not in captured.out


def test_cli_gates_on_phase_1_2_structure(tmp_path, capsys):
    path = _write_csv(tmp_path, {})

    assert audit_data_quality.main([str(path)]) == 1

    output = capsys.readouterr().out
    assert "Audit status: NOT RUN. Schema gate failed." in output
    assert "Data record count mismatch" in output
    assert "Records audited:" not in output
