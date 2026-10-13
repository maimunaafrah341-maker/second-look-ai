"""Tests for reading a local .env file."""

import os

from app.env import load_env_file


def test_missing_file_changes_nothing(tmp_path):
    assert load_env_file(tmp_path / ".env") == []


def test_values_are_read_and_existing_variables_are_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("SL_TEST_KEPT", "from-the-host")
    for name in ("SL_TEST_PLAIN", "SL_TEST_QUOTED", "SL_TEST_SPACED", "SL_TEST_EMPTY"):
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / ".env"
    path.write_text(
        "# a comment\n"
        "\n"
        "SL_TEST_PLAIN=abc=123\n"
        'SL_TEST_QUOTED="quoted value"\n'
        "  SL_TEST_SPACED =  spaced  \n"
        "SL_TEST_EMPTY=\n"
        "SL_TEST_KEPT=from-the-file\n"
        "not a setting\n",
        encoding="utf-8",
    )

    try:
        assert load_env_file(path) == ["SL_TEST_PLAIN", "SL_TEST_QUOTED", "SL_TEST_SPACED"]
        assert os.environ["SL_TEST_PLAIN"] == "abc=123"
        assert os.environ["SL_TEST_QUOTED"] == "quoted value"
        assert os.environ["SL_TEST_SPACED"] == "spaced"
        assert "SL_TEST_EMPTY" not in os.environ
        assert os.environ["SL_TEST_KEPT"] == "from-the-host"
    finally:
        for name in ("SL_TEST_PLAIN", "SL_TEST_QUOTED", "SL_TEST_SPACED"):
            os.environ.pop(name, None)


def test_a_file_saved_by_notepad_with_a_byte_order_mark_is_read(tmp_path, monkeypatch):
    monkeypatch.delenv("SL_TEST_BOM", raising=False)
    path = tmp_path / ".env"
    path.write_bytes(b"\xef\xbb\xbfSL_TEST_BOM=value\r\n")

    try:
        assert load_env_file(path) == ["SL_TEST_BOM"]
    finally:
        os.environ.pop("SL_TEST_BOM", None)
