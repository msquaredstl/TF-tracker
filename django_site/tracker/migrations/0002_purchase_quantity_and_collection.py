from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError, migrations


def _table_column_names(connection, table):
    try:
        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(cursor, table)
    except DatabaseError:
        return None
    return {
        getattr(col, "name", getattr(col, "column_name", "")).lower() for col in description
    }


def add_purchase_columns(apps, schema_editor):
    connection = schema_editor.connection
    existing_columns = _table_column_names(connection, "purchase")
    if existing_columns is None:
        return
    with connection.cursor() as cursor:
        if "qty" not in existing_columns:
            cursor.execute("ALTER TABLE purchase ADD COLUMN qty INTEGER DEFAULT 1")
        if "collection_id" not in existing_columns:
            cursor.execute("ALTER TABLE purchase ADD COLUMN collection_id INTEGER")


def populate_purchase_defaults(apps, schema_editor):
    connection = schema_editor.connection
    existing_columns = _table_column_names(connection, "purchase")
    if existing_columns is None:
        return

    try:
        user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    except ValueError as exc:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL must be of the form 'app_label.ModelName'"
        ) from exc

    UserModel = apps.get_model(user_app_label, user_model_name)
    Collection = apps.get_model("tracker", "Collection")

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

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE purchase SET collection_id = ? WHERE collection_id IS NULL",
            [collection.pk],
        )
        cursor.execute(
            "UPDATE purchase SET qty = 1 WHERE qty IS NULL OR qty = 0",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_create_collection"),
    ]

    operations = [
        migrations.RunPython(add_purchase_columns, migrations.RunPython.noop),
        migrations.RunPython(populate_purchase_defaults, migrations.RunPython.noop),
    ]
