import pytest

from app.db.session import DEFAULT_SQLITE_URL
from app.importers.import_csv import ensure_database_target


def test_refuses_default_sqlite_without_override() -> None:
    with pytest.raises(SystemExit) as excinfo:
        ensure_database_target(DEFAULT_SQLITE_URL, allow_sqlite=False)

    message = str(excinfo.value)
    assert "sqlite" in message.lower()


def test_allows_sqlite_when_flag_enabled() -> None:
    ensure_database_target(DEFAULT_SQLITE_URL, allow_sqlite=True)


def test_allows_non_default_database() -> None:
    ensure_database_target("sqlite:///:memory:", allow_sqlite=False)
