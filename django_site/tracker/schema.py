"""Helpers for inspecting and adapting to the legacy database schema."""

from __future__ import annotations

from functools import lru_cache

from django.db import connection
from django.db.utils import DatabaseError, OperationalError, ProgrammingError


@lru_cache(maxsize=None)
def table_column_names(table_name: str) -> frozenset[str]:
    """Return the lower-cased column names exposed by *table_name*."""

    try:
        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(
                cursor, table_name
            )
    except (ProgrammingError, OperationalError, DatabaseError):
        return frozenset()

    names: set[str] = set()
    for column in description:
        name = getattr(column, "name", "")
        if not name and hasattr(column, "column_name"):
            # Older Django/DB backends expose ``column_name`` instead of ``name``.
            name = getattr(column, "column_name")  # pragma: no cover - safety net
        if name:
            names.add(name.lower())
    return frozenset(names)


def table_has_column(table_name: str, column_name: str) -> bool:
    """Return ``True`` when *table_name* exposes *column_name*."""

    return column_name.lower() in table_column_names(table_name)


def _purchase_table_name() -> str:
    from .models import Purchase

    return Purchase._meta.db_table


def purchase_column_names() -> frozenset[str]:
    return table_column_names(_purchase_table_name())


def purchase_has_column(column_name: str) -> bool:
    return table_has_column(_purchase_table_name(), column_name)


def purchase_has_order_date() -> bool:
    return purchase_has_column("order_date")


def purchase_has_ship_date() -> bool:
    return purchase_has_column("ship_date")


def purchase_has_quantity() -> bool:
    return purchase_has_column("qty") or purchase_has_column("quantity")


def purchase_has_collection() -> bool:
    return purchase_has_column("collection_id")


def clear_purchase_cache() -> None:
    """Reset cached schema information for the purchase table."""

    table_column_names.cache_clear()
