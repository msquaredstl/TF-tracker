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


class Vendor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "vendor"

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.name


class Faction(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "faction"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "team"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Character(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    faction = models.ForeignKey(
        Faction,
        related_name="characters",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_column="faction_id",
    )

    class Meta:
        managed = False
        db_table = "character"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class CharacterTeam(models.Model):
    character = models.ForeignKey(
        Character,
        related_name="team_links",
        on_delete=models.CASCADE,
        db_column="character_id",
    )
    team = models.ForeignKey(
        Team,
        related_name="character_links",
        on_delete=models.CASCADE,
        db_column="team_id",
    )

    class Meta:
        managed = False
        db_table = "characterteam"
        unique_together = ("character", "team")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.character} ↔ {self.team}"


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False
        db_table = "tag"

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


class ItemCharacter(models.Model):
    item = models.ForeignKey(
        Item,
        related_name="character_links",
        on_delete=models.CASCADE,
        db_column="item_id",
    )
    character = models.ForeignKey(
        Character,
        related_name="item_links",
        on_delete=models.CASCADE,
        db_column="character_id",
    )
    is_primary = models.BooleanField(default=False)
    role = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "itemcharacter"
        unique_together = ("item", "character")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.item} ↔ {self.character}"


class ItemTag(models.Model):
    item = models.ForeignKey(
        Item,
        related_name="tag_links",
        on_delete=models.CASCADE,
        db_column="item_id",
    )
    tag = models.ForeignKey(
        Tag,
        related_name="item_links",
        on_delete=models.CASCADE,
        db_column="tag_id",
    )

    class Meta:
        managed = False
        db_table = "itemtag"
        unique_together = ("item", "tag")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.item} ↔ {self.tag}"


class Purchase(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(
        Item,
        related_name="purchases",
        on_delete=models.CASCADE,
        db_column="item_id",
    )
    vendor = models.ForeignKey(
        Vendor,
        related_name="purchases",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_column="vendor_id",
    )
    order_date = models.DateField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    ship_date = models.DateField(null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    tax = models.FloatField(null=True, blank=True)
    shipping = models.FloatField(null=True, blank=True)
    currency = models.CharField(max_length=16, null=True, blank=True)
    order_number = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "purchase"

    def __str__(self) -> str:  # pragma: no cover
        return f"Purchase of {self.item}"
