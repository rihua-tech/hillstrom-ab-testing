import csv
from dataclasses import replace

from src import reconcile_assignments
from src.reconcile_assignments import count_in_sql, format_summary, reconcile_csv
from src.validate_schema import EXPECTED_FIELDS


def _write_assignments(path, labels):
    header = (*EXPECTED_FIELDS[1:], EXPECTED_FIELDS[0])
    with path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source)
        writer.writerow(header)
        for label in labels:
            writer.writerow(
                [label if name == "segment" else "OPAQUE,CELL" for name in header]
            )


def test_sql_and_python_counts_reconcile_exactly(tmp_path):
    path = tmp_path / "assignments.csv"
    _write_assignments(path, ["No E-Mail", "Mens E-Mail", "Womens E-Mail", "No E-Mail"])
    original = path.read_bytes()

    result = reconcile_csv(path, expected_records=4)

    assert result.issues == ()
    assert result.sql.total == result.python_total == result.sql.accounted_for == 4
    assert result.sql.by_arm == result.python_by_arm == {
        "No E-Mail": 2,
        "Mens E-Mail": 1,
        "Womens E-Mail": 1,
    }
    assert result.sql.missing == result.sql.illegal == 0
    assert path.read_bytes() == original
    output = format_summary(result)
    assert "Total | 4 | 4 | 0" in output
    assert "SQL reconciliation status: PASS" in output
    for hidden in ("OPAQUE", "conversion", "visit", "spend"):
        assert hidden not in output


def test_sql_accounts_for_missing_and_illegal_without_printing_labels(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "exceptions.csv"
    labels = ["No E-Mail", "", " \t", "\u2007", "PRIVATE_ILLEGAL", " Mens E-Mail "]
    _write_assignments(path, labels)

    result = reconcile_csv(path, expected_records=len(labels))

    assert result.sql.missing == 3
    assert result.sql.illegal == 2
    assert result.sql.accounted_for == result.sql.total == 6
    assert result.python_by_arm is None
    monkeypatch.setattr(reconcile_assignments, "reconcile_csv", lambda _: result)
    assert reconcile_assignments.main([str(path)]) == 2

    output = capsys.readouterr().out
    assert "SQLite missing assignments: 3" in output
    assert "SQLite illegal assignments: 2" in output
    assert "SQL reconciliation status: BLOCKED" in output
    assert "PRIVATE_ILLEGAL" not in output


def test_displaced_arm_counts_are_blocked_even_when_totals_agree(tmp_path, monkeypatch):
    path = tmp_path / "assignments.csv"
    _write_assignments(path, ["No E-Mail", "Mens E-Mail", "Womens E-Mail"])
    monkeypatch.setattr(
        reconcile_assignments, "count_assignments", lambda *_, **__: (0, 2, 1)
    )

    result = reconcile_csv(path, expected_records=3)

    assert result.sql.total == result.python_total == 3
    assert len(result.issues) == 2
    output = format_summary(result)
    assert "Mens E-Mail | 0 | 1 | 1" in output
    assert "No E-Mail | 2 | 1 | -1" in output
    assert "SQL reconciliation status: BLOCKED" in output


def test_total_mismatch_and_incomplete_accounting_are_detected(tmp_path, monkeypatch):
    path = tmp_path / "assignments.csv"
    _write_assignments(path, ["No E-Mail", "Mens E-Mail", "Womens E-Mail"])
    sql = count_in_sql(path)
    monkeypatch.setattr(
        reconcile_assignments, "count_in_sql", lambda _: replace(sql, total=4)
    )

    result = reconcile_csv(path, expected_records=3)

    assert "SQLite total differs from the Python schema count." in result.issues
    assert "SQLite assignment categories do not sum to the full total." in result.issues
    output = format_summary(result)
    assert "Total | 3 | 4 | 1" in output
    assert "SQL reconciliation status: BLOCKED" in output
