import pytest

from src.validate_schema import EXPECTED_FIELDS, main, validate_csv

FIELDS = ("first", "second")


def test_valid_csv_counts_logical_records_and_preserves_bytes(tmp_path):
    path = tmp_path / "valid.csv"
    original = b'second,first\r\n"comma,inside",a\r\n"two\r\nlines",b\r\n"""quoted""",c'
    path.write_bytes(original)

    result = validate_csv(path, expected_fields=FIELDS, expected_records=3)

    assert result.passed
    assert result.record_count == 3
    assert path.read_bytes() == original


def test_header_reports_missing_unexpected_and_duplicate_fields(tmp_path):
    path = tmp_path / "header.csv"
    path.write_text("first,first,unrecognized\nx,y,z\n", encoding="utf-8")

    result = validate_csv(path, expected_fields=FIELDS, expected_records=1)

    assert not result.passed
    assert result.record_count == 1
    assert "Missing header fields: second." in result.errors
    assert "Unexpected header field positions: 3." in result.errors
    assert "Duplicate header field positions: 1, 2." in result.errors
    assert "unrecognized" not in "\n".join(result.errors)


def test_empty_file_has_no_header(tmp_path):
    path = tmp_path / "empty.csv"
    path.touch()

    result = validate_csv(path, expected_fields=FIELDS, expected_records=0)

    assert result.record_count == 0
    assert result.errors == ("CSV header is missing.",)


@pytest.mark.parametrize(
    "record",
    ['"synthetic-marker', '"synthetic-marker"x,y', 'synthetic-marker",y'],
)
def test_malformed_csv_stops_without_exposing_values(tmp_path, record):
    path = tmp_path / "malformed.csv"
    path.write_text(f"first,second\n{record}\n", encoding="utf-8")

    result = validate_csv(path, expected_fields=FIELDS, expected_records=1)

    assert not result.passed
    assert result.record_count is None
    assert result.errors == ("Malformed CSV near physical line 2.",)


def test_wrong_width_records_including_blank_records_are_counted(tmp_path):
    path = tmp_path / "width.csv"
    path.write_text("first,second\na,b\nshort\n\nc,d,e\n", encoding="utf-8")

    result = validate_csv(path, expected_fields=FIELDS, expected_records=4)

    assert not result.passed
    assert result.record_count == 4
    assert result.errors == (
        "Wrong-width data records: 3. First at data record 2: expected 2 fields, "
        "found 1.",
    )


def test_cli_fails_on_record_count_mismatch(tmp_path, capsys):
    path = tmp_path / "count.csv"
    header = ",".join(EXPECTED_FIELDS)
    row = ",".join(["synthetic-marker"] * len(EXPECTED_FIELDS))
    path.write_text(f"{header}\n{row}\n", encoding="utf-8")

    assert main([str(path)]) == 1
    output = capsys.readouterr().out
    assert "Expected data records: 64000" in output
    assert "Observed data records: 1" in output
    assert "Data record count mismatch: expected 64000, found 1." in output
    assert "Status: FAIL" in output
    assert "synthetic-marker" not in output
