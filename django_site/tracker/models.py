"""Django ORM models that reuse the existing SQLModel tables."""
from __future__ import annotations

from django.db import connection, models


class Company(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "company"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.name


class Line(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(
        Company, related_name="lines", null=True, blank=True, on_delete=models.DO_NOTHING, db_column="company_id"
    )

    class Meta:
        managed = False
        db_table = "line"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.name


class Series(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "series"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class ItemType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "itemtype"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "category"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Character(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "character"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Item(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=255, null=True, blank=True)
    version = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    scale = models.CharField(max_length=255, null=True, blank=True)
    condition = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, default="Owned", null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)

    company = models.ForeignKey(
        Company, related_name="items", null=True, blank=True, on_delete=models.DO_NOTHING, db_column="company_id"
    )
    line = models.ForeignKey(
        Line, related_name="items", null=True, blank=True, on_delete=models.DO_NOTHING, db_column="line_id"
    )
    series = models.ForeignKey(
        Series, related_name="items", null=True, blank=True, on_delete=models.DO_NOTHING, db_column="series_id"
    )
    type = models.ForeignKey(
        ItemType, related_name="items", null=True, blank=True, on_delete=models.DO_NOTHING, db_column="type_id"
    )
    category = models.ForeignKey(
        Category, related_name="items", null=True, blank=True, on_delete=models.DO_NOTHING, db_column="category_id"
    )

    class Meta:
        managed = False
        db_table = "item"

    def character_rows(self) -> list[dict[str, object]]:
        """Return metadata about characters linked to this item."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id, c.name, ic.is_primary, ic.role
                FROM itemcharacter AS ic
                INNER JOIN character AS c ON c.id = ic.character_id
                WHERE ic.item_id = %s
                ORDER BY ic.is_primary DESC, LOWER(c.name)
                """,
                [self.pk],
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "is_primary": bool(row[2]),
                "role": row[3],
            }
            for row in rows
        ]

    @property
    def primary_character(self) -> Character | None:
        rows = self.character_rows()
        for row in rows:
            if row["is_primary"]:
                return Character.objects.filter(pk=row["id"]).first()
        if rows:
            return Character.objects.filter(pk=rows[0]["id"]).first()
        return None

    def __str__(self) -> str:  # pragma: no cover
        return self.name


