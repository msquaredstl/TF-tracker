from __future__ import annotations

from django.db import migrations


def _table_has_column(cursor, table: str, column: str) -> bool:
    description = cursor.connection.introspection.get_table_description(cursor, table)
    lowered = {
        getattr(col, "name", getattr(col, "column_name", "")).lower() for col in description
    }
    return column.lower() in lowered


def add_purchase_date_columns(apps, schema_editor) -> None:
    connection = schema_editor.connection
    added_order = False
    added_ship = False
    with connection.cursor() as cursor:
        if not _table_has_column(cursor, "purchase", "order_date"):
            cursor.execute("ALTER TABLE purchase ADD COLUMN order_date DATE")
            added_order = True
        if not _table_has_column(cursor, "purchase", "ship_date"):
            cursor.execute("ALTER TABLE purchase ADD COLUMN ship_date DATE")
            added_ship = True
        if added_order:
            cursor.execute(
                """
                UPDATE purchase
                SET order_date = purchase_date
                WHERE order_date IS NULL AND purchase_date IS NOT NULL
                """
            )
        if added_ship:
            cursor.execute(
                """
                UPDATE purchase
                SET ship_date = purchase_date
                WHERE ship_date IS NULL AND purchase_date IS NOT NULL
                """
            )


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0002_purchase_quantity_and_collection"),
    ]

    operations = [
        migrations.RunPython(add_purchase_date_columns, migrations.RunPython.noop),
    ]
