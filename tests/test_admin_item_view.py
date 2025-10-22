from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

from django.contrib import admin
from tracker.admin import ItemAdmin
from tracker.models import Item, ItemCharacter, ItemTag, Purchase


class DummyManager:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)


class DummyCharacterLink:
    def __init__(self, name: str, *, is_primary: bool = False, role: str | None = None):
        self.character = SimpleNamespace(name=name)
        self.is_primary = is_primary
        self.role = role


class DummyTagLink:
    def __init__(self, name: str):
        self.tag = SimpleNamespace(name=name)


class DummyPurchase:
    def __init__(
        self,
        *,
        vendor: str | None = None,
        collection: str | None = None,
        order_date: dt.date | None = None,
        purchase_date: dt.date | None = None,
        ship_date: dt.date | None = None,
        price: float | None = None,
        currency: str | None = None,
        quantity: int | None = None,
        order_number: str | None = None,
    ):
        self.vendor = SimpleNamespace(name=vendor) if vendor else None
        self.collection = SimpleNamespace(name=collection) if collection else None
        self.order_date = order_date
        self.purchase_date = purchase_date
        self.ship_date = ship_date
        self.price = price
        self.currency = currency
        self.quantity = quantity
        self.order_number = order_number


class DummyItem:
    def __init__(
        self,
        *,
        character_links: list[DummyCharacterLink] | None = None,
        tag_links: list[DummyTagLink] | None = None,
        purchases: list[DummyPurchase] | None = None,
    ):
        self.pk = 1
        self.character_links = DummyManager(character_links or [])
        self.tag_links = DummyManager(tag_links or [])
        self.purchases = DummyManager(purchases or [])


def test_item_admin_inlines_cover_related_models():
    inline_models = {inline.model for inline in ItemAdmin.inlines}
    assert inline_models == {ItemCharacter, ItemTag, Purchase}


def test_item_admin_readonly_fields_expose_related_overview():
    item_admin = ItemAdmin(Item, admin.site)
    for field_name in (
        "primary_character_display",
        "character_overview",
        "tag_overview",
        "purchase_overview",
    ):
        assert field_name in item_admin.readonly_fields


def test_primary_character_display_prefers_marked_primary():
    item_admin = ItemAdmin(Item, admin.site)
    item = DummyItem(
        character_links=[
            DummyCharacterLink("Bumblebee"),
            DummyCharacterLink("Optimus Prime", is_primary=True),
        ]
    )

    assert item_admin.primary_character_display(item) == "Optimus Prime"


def test_character_overview_lists_related_entries():
    item_admin = ItemAdmin(Item, admin.site)
    item = DummyItem(
        character_links=[
            DummyCharacterLink("Bumblebee", role="Scout"),
            DummyCharacterLink("Optimus Prime", is_primary=True, role="Leader"),
        ]
    )

    rendered = str(item_admin.character_overview(item))
    assert "Optimus Prime" in rendered
    assert "<strong>Optimus Prime</strong>" in rendered
    assert "Scout" in rendered


def test_tag_overview_lists_tag_names():
    item_admin = ItemAdmin(Item, admin.site)
    item = DummyItem(tag_links=[DummyTagLink("Autobot"), DummyTagLink("Leader")])

    assert item_admin.tag_overview(item) == "Autobot, Leader"


def test_purchase_overview_formats_purchase_details():
    item_admin = ItemAdmin(Item, admin.site)
    item = DummyItem(
        purchases=[
            DummyPurchase(
                vendor="Hasbro Pulse",
                collection="Main Shelf",
                order_date=dt.date(2023, 1, 5),
                purchase_date=dt.date(2023, 1, 20),
                ship_date=dt.date(2023, 1, 25),
                price=29.99,
                currency="USD",
                quantity=2,
                order_number="A123",
            )
        ]
    )

    rendered = str(item_admin.purchase_overview(item))
    assert "Hasbro Pulse" in rendered
    assert "ordered 2023-01-05" in rendered
    assert "collection Main Shelf" in rendered
    assert "order A123" in rendered
