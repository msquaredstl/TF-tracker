"""Tests for helper utilities in ``tracker.views``."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.db.utils import OperationalError, ProgrammingError

from tracker import views


class _DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def close(self):  # pragma: no cover - compatibility shim
        return None


def _install_table_description(monkeypatch, columns):
    """Patch ``tracker.views`` introspection helpers for testing."""

    def fake_cursor():
        return _DummyCursor()

    def fake_get_table_description(cursor, table_name):  # pragma: no cover - exercised indirectly
        if isinstance(columns, Exception):
            raise columns
        return [SimpleNamespace(name=name) for name in columns]

    monkeypatch.setattr(views.connection, "cursor", fake_cursor, raising=False)
    monkeypatch.setattr(
        views.connection.introspection,
        "get_table_description",
        fake_get_table_description,
        raising=False,
    )


@pytest.mark.parametrize(
    "columns, expected",
    [
        (["id", "order_date", "ship_date"], True),
        (["id", "purchase_date", "ship_date"], False),
    ],
)
def test_purchase_has_order_date_detects_column(monkeypatch, columns, expected):
    views._purchase_column_names.cache_clear()
    _install_table_description(monkeypatch, columns)
    assert views._purchase_has_order_date() is expected


@pytest.mark.parametrize("exc", [ProgrammingError("missing"), OperationalError("oops")])
def test_purchase_has_order_date_missing_table(monkeypatch, exc):
    views._purchase_column_names.cache_clear()
    _install_table_description(monkeypatch, exc)
    assert views._purchase_has_order_date() is False


@pytest.mark.parametrize(
    "columns, expected",
    [
        (["id", "ship_date", "purchase_date"], True),
        (["id", "purchase_date", "order_date"], False),
    ],
)
def test_purchase_has_ship_date_detects_column(monkeypatch, columns, expected):
    views._purchase_column_names.cache_clear()
    _install_table_description(monkeypatch, columns)
    assert views._purchase_has_ship_date() is expected


def test_purchase_annotations_fall_back_to_purchase_date(monkeypatch):
    monkeypatch.setattr(views, "_purchase_has_ship_date", lambda: False)
    monkeypatch.setattr(views, "_purchase_has_order_date", lambda: False)

    annotations = views._purchase_annotations()

    ship_expr = annotations["ship_date_value"]
    order_expr = annotations["order_date_value"]

    assert ship_expr is order_expr
    assert ship_expr.source_expressions[0].name == "purchases__purchase_date"


def test_purchase_annotations_include_ship_date_when_available(monkeypatch):
    monkeypatch.setattr(views, "_purchase_has_ship_date", lambda: True)
    monkeypatch.setattr(views, "_purchase_has_order_date", lambda: False)

    annotations = views._purchase_annotations()

    ship_expr = annotations["ship_date_value"]

    assert ship_expr.source_expressions[0].name == "purchases__ship_date"
