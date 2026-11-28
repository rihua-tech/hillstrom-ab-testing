import math
from dataclasses import replace

import pytest

from src import check_srm
from src.check_srm import ARMS, HOLD_THRESHOLD, count_assignments, pearson_srm


def test_equal_allocation_passes():
    result = pearson_srm((10_000, 10_000, 10_000))

    assert result.expected_per_arm == 10_000
    assert result.statistic == 0
    assert result.degrees_of_freedom == 2
    assert result.p_value == 1
    assert not result.hold


def test_lesson_example_reproduces_statistic_and_p_value():
    result = pearson_srm((10_400, 9_800, 9_800))

    assert result.statistic == pytest.approx(24)
    assert result.p_value == pytest.approx(0.000006144212353, rel=1e-9)
    assert result.hold


def test_clear_mismatch_returns_hold_exit(monkeypatch, capsys):
    monkeypatch.setattr(check_srm, "count_assignments", lambda _: (800, 100, 100))

    assert check_srm.main(["synthetic.csv"]) == 2
    output = capsys.readouterr().out
    assert "SRM status: HOLD" in output
    assert "Confirmatory interpretation: HOLD pending investigation" in output


def test_expected_count_is_not_rounded_to_an_integer():
    result = pearson_srm((3, 3, 4))

    assert result.expected_per_arm == 10 / 3
    assert result.statistic == pytest.approx(0.2)


@pytest.mark.parametrize(
    ("p_value", "hold"),
    [
        (math.nextafter(HOLD_THRESHOLD, 0), True),
        (HOLD_THRESHOLD, False),
        (math.nextafter(HOLD_THRESHOLD, 1), False),
    ],
)
def test_hold_threshold_is_strict(p_value, hold):
    result = replace(pearson_srm((10, 10, 10)), p_value=p_value)

    assert result.hold is hold


def test_count_reads_only_the_assignment_column_and_keeps_all_records(tmp_path):
    path = tmp_path / "assignments.csv"
    path.write_text(
        "visit,segment,conversion,spend\n"
        '"opaque,cell",Mens E-Mail,bad,hidden\n'
        "opaque,No E-Mail,bad,hidden\n"
        "opaque,Womens E-Mail,bad,hidden\n"
        "opaque,No E-Mail,bad,hidden\n",
        encoding="utf-8",
    )
    original = path.read_bytes()

    counts = count_assignments(path, expected_records=4)

    assert dict(zip(ARMS, counts, strict=True)) == {
        "No E-Mail": 2,
        "Mens E-Mail": 1,
        "Womens E-Mail": 1,
    }
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("label", "diagnostic"),
    [
        ("", "Missing segment"),
        (" \t", "Missing segment"),
        ("RAW_ILLEGAL_LABEL", "Illegal segment label"),
    ],
)
def test_bad_assignment_stops_before_reporting_a_test(
    tmp_path, capsys, label, diagnostic
):
    path = tmp_path / "invalid.csv"
    path.write_text(
        f"segment,other\nNo E-Mail,x\n{label},x\nWomens E-Mail,x\n",
        encoding="utf-8",
    )

    assert check_srm.main([str(path)]) == 1

    output = capsys.readouterr().out
    assert f"SRM status: NOT RUN. {diagnostic} at data record 2." in output
    assert "RAW_ILLEGAL_LABEL" not in output
    assert "p-value:" not in output
    assert "Assignments counted:" not in output
