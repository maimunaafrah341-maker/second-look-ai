"""Tests for the ingestion logic.

The messages below are tiny parser fixtures written for these tests. They are
not dataset records and are never used for training.
"""

import zipfile

import pytest

from ingest_sms_spam import (
    IngestionError,
    Record,
    parse,
    read_csv,
    read_member,
    summarize,
    write_csv,
)


def test_parse_keeps_text_and_labels_unchanged():
    raw = 'ham\tHello,  "you"\tthere \nspam\tWIN £100 now!!\n'.encode("utf-8")

    result = parse(raw)

    assert result.excluded == []
    assert result.records == [
        Record(id=1, label="ham", text='Hello,  "you"\tthere '),
        Record(id=2, label="spam", text="WIN £100 now!!"),
    ]


def test_parse_reports_excluded_lines_with_reasons():
    raw = b"ham\tfine\nno separator here\nmaybe\tunknown label\nspam\t   \n\nham\tlast\n"

    result = parse(raw)

    assert [record.id for record in result.records] == [1, 6]
    assert result.excluded == [
        (2, "no tab separator"),
        (3, "unknown label 'maybe'"),
        (4, "empty message"),
        (5, "blank line"),
    ]


def test_parse_handles_missing_final_newline_and_crlf():
    result = parse(b"ham\tone\r\nspam\ttwo")

    assert [record.text for record in result.records] == ["one", "two"]
    assert result.excluded == []


def test_parse_rejects_invalid_utf8():
    with pytest.raises(IngestionError, match="not valid UTF-8"):
        parse(b"ham\t\xff\xfe\n")


def test_summarize_counts_duplicates_without_removing_them():
    records = parse(b"ham\tsame\nham\tsame\nspam\tsame\nspam\tother\nham\tSame\n").records

    summary = summarize(records)

    assert summary["records"] == 5
    assert summary["labels"] == {"ham": 3, "spam": 2}
    assert summary["unique_texts"] == 3
    assert summary["duplicate_records"] == 2
    assert summary["texts_appearing_more_than_once"] == 1
    assert summary["texts_with_conflicting_labels"] == 1


def test_csv_round_trip_and_rerun_does_not_duplicate(tmp_path):
    records = parse('ham\tline with, comma and "quotes"\nspam\ttwo\n'.encode("utf-8")).records
    destination = tmp_path / "out.csv"

    write_csv(records, destination)
    write_csv(records, destination)

    assert read_csv(destination) == records
    assert not list(tmp_path.glob("*.part"))


def test_read_member_returns_file_contents(tmp_path):
    archive = tmp_path / "ok.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("SMSSpamCollection", "ham\thi\n")

    assert read_member(archive, "SMSSpamCollection") == b"ham\thi\n"


@pytest.mark.parametrize("name", ["../evil.txt", "/absolute.txt", "nested/../../evil.txt", "C:/evil.txt"])
def test_read_member_rejects_unsafe_paths(tmp_path, name):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("SMSSpamCollection", "ham\thi\n")
        zf.writestr(name, "x")

    with pytest.raises(IngestionError, match="unsafe path"):
        read_member(archive, "SMSSpamCollection")


def test_read_member_reports_missing_file(tmp_path):
    archive = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("readme", "x")

    with pytest.raises(IngestionError, match="does not contain"):
        read_member(archive, "SMSSpamCollection")
