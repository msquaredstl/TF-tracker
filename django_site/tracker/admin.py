from __future__ import annotations

from typing import Dict, Tuple

from django.contrib import admin, messages
from django.db import transaction

from .models import (
    Category,
    Character,
    CharacterTeam,
    Company,
    Faction,
    Item,
    ItemCharacter,
    ItemTag,
    ItemType,
    Line,
    Purchase,
    Series,
    Tag,
    Team,
    Vendor,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "company")
    list_filter = ("company",)


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "faction")
    list_filter = ("faction",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(CharacterTeam)
class CharacterTeamAdmin(admin.ModelAdmin):
    list_display = ("character", "team")
    search_fields = ("character__name", "team__name")
    list_filter = ("team",)


@admin.register(ItemCharacter)
class ItemCharacterAdmin(admin.ModelAdmin):
    list_display = ("item", "character", "is_primary")
    search_fields = ("item__name", "character__name")
    list_filter = ("is_primary", "character__faction")


@admin.register(ItemTag)
class ItemTagAdmin(admin.ModelAdmin):
    list_display = ("item", "tag")
    search_fields = ("item__name", "tag__name")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "vendor",
        "order_date",
        "purchase_date",
        "ship_date",
        "price",
    )
    search_fields = ("item__name", "vendor__name", "order_number")
    list_filter = ("vendor", "order_date", "ship_date")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "line", "series", "status")
    list_filter = ("status", "company", "line", "series", "type", "category")
    search_fields = ("name", "sku", "notes")
    actions = ("deduplicate_items",)

    @admin.action(description="Deduplicate fully matching items")
    def deduplicate_items(self, request, queryset):
        signature_map: Dict[Tuple[object, ...], Item] = {}
        removed = 0

        tracked_fields = (
            "name",
            "sku",
            "version",
            "year",
            "scale",
            "condition",
            "status",
            "location",
            "url",
            "notes",
            "company_id",
            "line_id",
            "series_id",
            "type_id",
            "category_id",
        )

        with transaction.atomic():
            for item in queryset.select_related(
                "company", "line", "series", "type", "category"
            ).order_by("pk"):
                signature = tuple(getattr(item, field) for field in tracked_fields)
                keeper = signature_map.setdefault(signature, item)
                if keeper.pk == item.pk:
                    continue

                Purchase.objects.filter(item=item).update(item=keeper)
                ItemCharacter.objects.filter(item=item).update(item=keeper)
                ItemTag.objects.filter(item=item).update(item=keeper)
                item.delete()
                removed += 1

        if removed:
            self.message_user(request, f"Removed {removed} duplicate item(s).")
        else:
            self.message_user(request, "No duplicate items found.", level=messages.INFO)
