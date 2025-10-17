from __future__ import annotations

from tracker import models as dj_models


def test_item_fields_cover_sheet_attributes():
    item_field_names = {field.name for field in dj_models.Item._meta.get_fields()}

    expected_item_fields = {
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
        "company",
        "line",
        "series",
        "type",
        "category",
        "character_links",
        "purchases",
    }

    assert expected_item_fields.issubset(item_field_names)


def test_purchase_fields_cover_sheet_attributes():
    purchase_field_names = {field.name for field in dj_models.Purchase._meta.get_fields()}

    expected_purchase_fields = {
        "order_date",
        "purchase_date",
        "ship_date",
        "price",
        "tax",
        "shipping",
        "currency",
        "order_number",
        "notes",
        "vendor",
        "quantity",
        "collection",
    }

    assert expected_purchase_fields.issubset(purchase_field_names)
