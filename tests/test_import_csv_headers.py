from __future__ import annotations

import csv
from pathlib import Path

from app.importers.import_csv import build_header_map


def test_sheet1_headers_map_to_known_fields():
    csv_path = Path("Sheet1.csv")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader)

    header_map = build_header_map(headers)

    assert header_map["name"] == "Name"
    assert header_map["sku"] == "SKU"
    assert header_map["primary_character"] == "Character"
    assert header_map["characters"] == "Additional Characters"
    assert header_map["faction"] == "Faction"
    assert header_map["series"] == "Series"
    assert header_map["line"] == "Line"
    assert header_map["company"] == "Company"
    assert header_map["type"] == "Type"
    assert header_map["category"] == "Category"
    assert header_map["order_date"] == "Order Date"
    assert header_map["ship_date"] == "Ship Date"
    assert header_map["vendor"] == "Vendor"
    assert header_map["order_number"] == "Order #"
    assert header_map["price"] == "Price"
    assert header_map["notes"] == "notes"
