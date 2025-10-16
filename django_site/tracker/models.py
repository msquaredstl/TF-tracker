"""Django ORM models that reuse the existing SQLModel tables."""
from __future__ import annotations

from django.db import models


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

    @property
    def primary_character(self) -> Character | None:
        link = self.character_links.filter(is_primary=True).select_related("character").first()
        if link:
            return link.character
        return None

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class ItemCharacter(models.Model):
    item = models.ForeignKey(Item, related_name="character_links", on_delete=models.CASCADE, db_column="item_id")
    character = models.ForeignKey(Character, related_name="item_links", on_delete=models.CASCADE, db_column="character_id")
    is_primary = models.BooleanField(default=False)
    role = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "itemcharacter"
        unique_together = ("item", "character")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.item} — {self.character}"
