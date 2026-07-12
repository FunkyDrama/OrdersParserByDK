"""Tests for the automatic cleanup of old log files."""

from datetime import date

from core.console import cleanup_old_logs


def _touch(directory, name):
    path = directory / name
    path.write_text("log", encoding="utf-8")
    return path


def test_deletes_only_logs_older_than_retention(tmp_path):
    today = date(2026, 7, 5)
    old = _touch(tmp_path, "parser_2026-06-20.log")
    boundary = _touch(tmp_path, "parser_2026-06-28.log")
    fresh = _touch(tmp_path, "parser_2026-07-04.log")
    current = _touch(tmp_path, "parser_2026-07-05.log")

    deleted = cleanup_old_logs(str(tmp_path), max_age_days=7, today=today)

    assert deleted == 1
    assert not old.exists()
    assert boundary.exists()
    assert fresh.exists()
    assert current.exists()


def test_ignores_foreign_files(tmp_path):
    keep_me = _touch(tmp_path, "important.txt")
    weird = _touch(tmp_path, "parser_not-a-date.log")
    other_log = _touch(tmp_path, "backup_2020-01-01.log")

    deleted = cleanup_old_logs(str(tmp_path), max_age_days=7, today=date(2026, 7, 5))

    assert deleted == 0
    assert keep_me.exists()
    assert weird.exists()
    assert other_log.exists()


def test_missing_directory_is_fine(tmp_path):
    assert cleanup_old_logs(str(tmp_path / "no-such-folder")) == 0


def test_uses_default_retention_from_constants(tmp_path):
    from core.constants import LOG_RETENTION_DAYS

    assert LOG_RETENTION_DAYS == 3
    _touch(tmp_path, "parser_2020-01-01.log")
    deleted = cleanup_old_logs(str(tmp_path), today=date(2026, 7, 5))
    assert deleted == 1
