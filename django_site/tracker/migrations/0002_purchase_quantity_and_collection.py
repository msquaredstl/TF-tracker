from __future__ import annotations

from django.conf import settings
from django.db import migrations


def _table_has_column(cursor, table, column):
    description = cursor.connection.introspection.get_table_description(cursor, table)
    lowered = {
        getattr(col, "name", getattr(col, "column_name", "")).lower() for col in description
    }
    return column.lower() in lowered


def add_purchase_columns(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        if not _table_has_column(cursor, "purchase", "qty"):
            cursor.execute("ALTER TABLE purchase ADD COLUMN qty INTEGER DEFAULT 1")
        if not _table_has_column(cursor, "purchase", "collection_id"):
            cursor.execute("ALTER TABLE purchase ADD COLUMN collection_id INTEGER")


def populate_purchase_defaults(apps, schema_editor):
    UserModel = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Collection = apps.get_model("tracker", "Collection")
    Purchase = apps.get_model("tracker", "Purchase")

    user = UserModel.objects.order_by("pk").first()
    if not user:
        return

    display_name = getattr(user, "get_full_name", lambda: "")()
    if not display_name:
        display_name = user.get_username()

    collection, _ = Collection.objects.get_or_create(
        user=user,
        defaults={"name": f"{display_name}'s Collection"},
    )

    Purchase.objects.filter(collection_id__isnull=True).update(collection_id=collection.pk)
    Purchase.objects.filter(quantity__isnull=True).update(quantity=1)


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_create_collection"),
    ]

    operations = [
        migrations.RunPython(add_purchase_columns, migrations.RunPython.noop),
        migrations.RunPython(populate_purchase_defaults, migrations.RunPython.noop),
    ]
