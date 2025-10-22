from __future__ import annotations

from typing import Dict, Tuple

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Prefetch
from django.utils.html import format_html, format_html_join

from .models import (
    Category,
    Character,
    CharacterTeam,
    Collection,
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


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username", "user__email")


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


class ItemCharacterInline(admin.TabularInline):
    model = ItemCharacter
    extra = 0
    autocomplete_fields = ("character",)
    fields = ("character", "role", "is_primary")
    ordering = ("-is_primary", "character__name")
    show_change_link = True


class ItemTagInline(admin.TabularInline):
    model = ItemTag
    extra = 0
    autocomplete_fields = ("tag",)
    fields = ("tag",)
    ordering = ("tag__name",)
    show_change_link = True


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 0
    autocomplete_fields = ("vendor", "collection")
    fields = (
        "vendor",
        "collection",
        "order_date",
        "purchase_date",
        "ship_date",
        "price",
        "tax",
        "shipping",
        "currency",
        "order_number",
        "quantity",
        "notes",
    )
    ordering = ("-purchase_date", "-order_date", "pk")
    show_change_link = True


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "vendor",
        "order_date",
        "purchase_date",
        "ship_date",
        "price",
        "quantity",
        "collection",
    )
    search_fields = ("item__name", "vendor__name", "order_number", "collection__name")
    list_filter = ("vendor", "order_date", "ship_date", "collection")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = (ItemCharacterInline, ItemTagInline, PurchaseInline)
    list_display = (
        "name",
        "company",
        "line",
        "series",
        "status",
        "primary_character_display",
    )
    list_filter = (
        "status",
        "company",
        "line",
        "series",
        "type",
        "category",
    )
    search_fields = (
        "name",
        "sku",
        "notes",
        "character_links__character__name",
        "tag_links__tag__name",
        "purchases__vendor__name",
        "purchases__order_number",
    )
    list_select_related = ("company", "line", "series", "type", "category")
    autocomplete_fields = ("company", "line", "series", "type", "category")
    readonly_fields = (
        "primary_character_display",
        "character_overview",
        "tag_overview",
        "purchase_overview",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "status",
                    "company",
                    "line",
                    "series",
                    "type",
                    "category",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "sku",
                    "version",
                    "year",
                    "scale",
                    "condition",
                    "location",
                    "url",
                    "notes",
                    "extra",
                )
            },
        ),
        (
            "Related data overview",
            {
                "fields": (
                    "primary_character_display",
                    "character_overview",
                    "tag_overview",
                    "purchase_overview",
                )
            },
        ),
    )
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            Prefetch(
                "character_links",
                queryset=ItemCharacter.objects.select_related("character").order_by(
                    "-is_primary", "character__name"
                ),
            ),
            Prefetch(
                "tag_links",
                queryset=ItemTag.objects.select_related("tag").order_by("tag__name"),
            ),
            Prefetch(
                "purchases",
                queryset=Purchase.objects.select_related(
                    "vendor", "collection"
                ).order_by("-purchase_date", "-order_date", "pk"),
            ),
        ).select_related("company", "line", "series", "type", "category")

    def _character_links(self, obj: Item) -> list[ItemCharacter]:
        if not getattr(obj, "pk", None):
            return []
        return list(obj.character_links.all())

    def _tag_links(self, obj: Item) -> list[ItemTag]:
        if not getattr(obj, "pk", None):
            return []
        return list(obj.tag_links.all())

    def _purchases(self, obj: Item) -> list[Purchase]:
        if not getattr(obj, "pk", None):
            return []
        return list(obj.purchases.all())

    @admin.display(description="Primary character")
    def primary_character_display(self, obj: Item) -> str:
        links = self._character_links(obj)
        for link in links:
            if link.is_primary and getattr(link, "character", None):
                return link.character.name
        for link in links:
            if getattr(link, "character", None):
                return link.character.name
        return "—"

    @admin.display(description="Linked characters")
    def character_overview(self, obj: Item) -> str:
        links = [
            link
            for link in self._character_links(obj)
            if getattr(link, "character", None)
        ]
        if not links:
            return "—"

        def render(link: ItemCharacter) -> str:
            name = link.character.name
            label = (
                format_html("<strong>{}</strong>", name)
                if link.is_primary
                else format_html("{}", name)
            )
            details: list[str] = []
            if link.role:
                details.append(link.role)
            if details:
                return format_html(
                    "{}<br><small>{}</small>", label, " • ".join(details)
                )
            return label

        return format_html_join("<br>", "{}", ((render(link),) for link in links))

    @admin.display(description="Tags")
    def tag_overview(self, obj: Item) -> str:
        tags = [
            link.tag.name for link in self._tag_links(obj) if getattr(link, "tag", None)
        ]
        if not tags:
            return "—"
        return ", ".join(tags)

    @admin.display(description="Purchases")
    def purchase_overview(self, obj: Item) -> str:
        purchases = self._purchases(obj)
        if not purchases:
            return "—"

        def render(purchase: Purchase) -> str:
            vendor_name = (
                purchase.vendor.name if getattr(purchase, "vendor", None) else "—"
            )
            details: list[str] = []
            if purchase.order_date:
                details.append(f"ordered {purchase.order_date:%Y-%m-%d}")
            if purchase.purchase_date:
                details.append(f"purchased {purchase.purchase_date:%Y-%m-%d}")
            if purchase.ship_date:
                details.append(f"shipped {purchase.ship_date:%Y-%m-%d}")
            if purchase.price is not None:
                currency = f" {purchase.currency}" if purchase.currency else ""
                details.append(f"price {purchase.price:,.2f}{currency}")
            if purchase.quantity not in (None, 1):
                details.append(f"qty {purchase.quantity}")
            if getattr(purchase, "collection", None):
                details.append(f"collection {purchase.collection.name}")
            if purchase.order_number:
                details.append(f"order {purchase.order_number}")
            detail_block = " • ".join(details)
            if detail_block:
                return format_html(
                    "<strong>{}</strong><br><small>{}</small>",
                    vendor_name,
                    detail_block,
                )
            return format_html("<strong>{}</strong>", vendor_name)

        return format_html_join(
            "<br><br>", "{}", ((render(purchase),) for purchase in purchases)
        )
