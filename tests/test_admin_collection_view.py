"""Tests covering the Django admin collection integrations."""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

from django.contrib import admin
from django.contrib.auth import get_user_model
from tracker.admin import (
    CollectionAdmin,
    CollectionInline,
    CollectionPurchaseInline,
    TrackerUserAdmin,
    render_collection_items,
    render_collection_orders,
)
from tracker.models import Collection, Purchase


class DummyManager:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return list(self._items)

    def select_related(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self._items)

    def count(self):
        return len(self._items)


class DummyCompany:
    def __init__(self, name: str):
        self.name = name


class DummyItem:
    def __init__(
        self,
        name: str,
        *,
        pk: int | None = None,
        status: str | None = None,
        company: DummyCompany | None = None,
    ):
        self.name = name
        self.pk = pk
        self.status = status
        self.company = company


class DummyVendor:
    def __init__(self, name: str):
        self.name = name


class DummyPurchase:
    def __init__(
        self,
        *,
        item: DummyItem | None = None,
        vendor: DummyVendor | None = None,
        order_date: dt.date | None = None,
        purchase_date: dt.date | None = None,
        ship_date: dt.date | None = None,
        price: float | None = None,
        currency: str | None = None,
        quantity: int | None = None,
        order_number: str | None = None,
    ):
        self.item = item
        self.vendor = vendor
        self.order_date = order_date
        self.purchase_date = purchase_date
        self.ship_date = ship_date
        self.price = price
        self.currency = currency
        self.quantity = quantity
        self.order_number = order_number


class DummyCollection:
    def __init__(self, purchases: list[DummyPurchase] | None = None):
        self.pk = 1
        self.purchases = DummyManager(purchases or [])


def test_collection_admin_uses_purchase_inline():
    inline_models = {inline.model for inline in CollectionAdmin.inlines}
    assert inline_models == {Purchase}


def test_collection_purchase_inline_configuration():
    inline = CollectionPurchaseInline(Collection, admin.site)
    assert inline.fk_name == "collection"
    assert "item" in inline.autocomplete_fields
    assert "vendor" in inline.autocomplete_fields


def test_collection_admin_readonly_fields_include_overviews():
    collection_admin = CollectionAdmin(Collection, admin.site)
    assert "item_overview" in collection_admin.readonly_fields
    assert "order_overview" in collection_admin.readonly_fields


def test_collection_admin_item_overview_lists_items():
    collection_admin = CollectionAdmin(Collection, admin.site)
    collection = DummyCollection(
        purchases=[
            DummyPurchase(
                item=DummyItem(
                    "Optimus Prime",
                    pk=1,
                    status="Owned",
                    company=DummyCompany("Hasbro"),
                ),
                quantity=2,
            ),
            DummyPurchase(
                item=DummyItem("Megatron", status="Wishlist"),
                quantity=1,
            ),
        ]
    )

    rendered = str(collection_admin.item_overview(collection))
    assert "Optimus Prime" in rendered
    assert "qty 2" in rendered
    assert "Hasbro" in rendered
    assert "Megatron" in rendered


def test_collection_admin_order_overview_formats_purchase_details():
    collection_admin = CollectionAdmin(Collection, admin.site)
    collection = DummyCollection(
        purchases=[
            DummyPurchase(
                item=DummyItem("Optimus Prime", pk=1),
                vendor=DummyVendor("Hasbro Pulse"),
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

    rendered = str(collection_admin.order_overview(collection))
    assert "Hasbro Pulse" in rendered
    assert "ordered 2023-01-05" in rendered
    assert "price 29.99 USD" in rendered
    assert "qty 2" in rendered
    assert "order A123" in rendered


def test_collection_inline_reuses_render_helpers():
    inline = CollectionInline(Collection, admin.site)
    collection = DummyCollection(
        purchases=[DummyPurchase(item=DummyItem("Starscream"))]
    )

    assert "Starscream" in str(inline.items_summary(collection))
    assert "Starscream" in str(inline.orders_summary(collection))


def test_render_helpers_handle_empty_collection():
    collection = DummyCollection()
    assert render_collection_items(collection) == "—"
    assert render_collection_orders(collection) == "—"


def test_collection_admin_counts_use_annotations_when_available():
    collection_admin = CollectionAdmin(Collection, admin.site)
    annotated = SimpleNamespace(
        _item_count=3, _order_count=4, purchases=DummyManager([])
    )
    assert collection_admin.item_count(annotated) == 3
    assert collection_admin.order_count(annotated) == 4


def test_user_admin_registers_collection_inline():
    user_model = get_user_model()
    user_admin = admin.site._registry[user_model]
    assert CollectionInline in user_admin.inlines
    assert isinstance(user_admin, TrackerUserAdmin)


def test_user_admin_collection_name_handles_missing_collection():
    user_model = get_user_model()
    user_admin = admin.site._registry[user_model]
    user = SimpleNamespace(collection=None)
    assert user_admin.collection_name(user) == "—"
