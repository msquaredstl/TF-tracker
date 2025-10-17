import csv
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from sqlmodel import Session, select
from app.db.session import DEFAULT_SQLITE_URL, DB_URL, engine, init_db
from app.models import (
    Item, Company, Line, Series, ItemType, Category, Character, ItemCharacter,
    Vendor, Purchase, Faction
)
from app.utils import get_or_create, split_characters

DEFAULT_MAP = {
  "name": ["name","figure","character","title"],
  "company": ["company","manufacturer","brand"],
  "line": ["line","series (product line)","sub-line","subline","brand line"],
  "series": ["series","media","source"],
  "type": ["type","kind"],
  "category": ["category","class","scale category"],
  "sku": ["sku","code","id","figure id"],
  "version": ["version","release","variant"],
  "year": ["year","release year"],
  "order_date": ["order date","ordered"],
  "purchase_date": ["purchase date","bought","date"],
  "ship_date": ["ship date","shipped"],
  "price": ["price","paid","cost"],
  "tax": ["tax","sales tax"],
  "shipping": ["shipping","postage"],
  "currency": ["currency"],
  "order_number": ["order","order number"],
  "vendor": ["vendor","store","source","retailer","marketplace"],
  "condition": ["condition","state"],
  "status": ["status","owned/sold/preorder","owned","preorder","sold","wishlist"],
  "location": ["location","shelf","bin","box"],
  "url": ["url","link"],
  "characters": ["characters","character list","additional characters"],
  "faction": ["faction","allegiance"],
  "notes": ["notes","comments"]
}

def normalize(s: str) -> str:
    return s.strip().lower()

def build_header_map(headers: List[str], user_map: Optional[Dict[str, List[str]]] = None) -> Dict[str, Optional[str]]:
    mapping = {}
    hdr_norm = {normalize(h): h for h in headers}
    merged = DEFAULT_MAP.copy()
    if user_map:
        for k,v in user_map.items():
            merged[k] = v
    for field, aliases in merged.items():
        found = None
        for a in aliases:
            a_norm = normalize(a)
            if a_norm in hdr_norm:
                found = hdr_norm[a_norm]
                break
        mapping[field] = found
    return mapping

def parse_date(val: str) -> Optional[str]:
    from datetime import datetime
    val = (val or "").strip()
    if not val:
        return None
    fmts = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%d-%b-%Y"]
    for f in fmts:
        try:
            return datetime.strptime(val, f).date().isoformat()
        except Exception:
            pass
    return None

def to_float(val: str) -> Optional[float]:
    try:
        val = val.replace("$","").replace(",","").strip()
        return float(val) if val else None
    except Exception:
        return None

def to_int(val: str) -> Optional[int]:
    try:
        v = val.strip()
        return int(v) if v else None
    except Exception:
        return None

def ensure_database_target(db_url: str, allow_sqlite: bool) -> None:
    if not allow_sqlite and db_url == DEFAULT_SQLITE_URL:
        raise SystemExit(
            "Refusing to import into the local SQLite fallback. "
            "Set remote database credentials or pass --allow-sqlite to proceed."
        )


def main():
    parser = argparse.ArgumentParser(description="Import a CSV export into normalized tables.")
    parser.add_argument("csv_path", help="Path to the CSV file (exported from Google Sheets).")
    parser.add_argument("--map", dest="mapfile", help="Optional JSON mapping overrides.", default=None)
    parser.add_argument(
        "--allow-sqlite",
        action="store_true",
        help="Permit importing into the local SQLite fallback database.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    user_map = None
    if args.mapfile:
        with open(args.mapfile, "r", encoding="utf-8") as f:
            user_map = json.load(f)

    ensure_database_target(DB_URL, args.allow_sqlite)

    init_db()

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f, Session(engine) as session:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        header_map = build_header_map(headers, user_map)

        count = 0
        for row in reader:
            def get(field: str):
                h = header_map.get(field)
                return row.get(h) if h else None

            name = (get("name") or "").strip()
            if not name:
                continue

            company = get_or_create(session, Company, get("company"))
            line = get_or_create(session, Line, get("line"))
            if line and company and line.company_id is None:
                line.company_id = company.id
                session.add(line); session.commit()

            series = get_or_create(session, Series, get("series"))
            type_ = get_or_create(session, ItemType, get("type"))
            category = get_or_create(session, Category, get("category"))

            item = Item(
                name=name,
                sku=(get("sku") or None),
                version=(get("version") or None),
                year=to_int(get("year") or ""),
                scale=None,
                condition=(get("condition") or None),
                status=(get("status") or "Owned"),
                location=(get("location") or None),
                url=(get("url") or None),
                notes=(get("notes") or None),
                company_id=company.id if company else None,
                line_id=line.id if line else None,
                series_id=series.id if series else None,
                type_id=type_.id if type_ else None,
                category_id=category.id if category else None,
            )
            session.add(item); session.commit(); session.refresh(item)

            # characters
            chars = split_characters(get("characters"))
            faction_hint = get("faction")
            faction_obj = get_or_create(session, Faction, faction_hint) if faction_hint else None

            primary_set = False
            for idx, raw in enumerate(chars):
                nm = raw
                is_primary = False
                if "|" in raw:
                    parts = [p.strip() for p in raw.split("|")]
                    nm = parts[0]
                    is_primary = any(p.lower() == "primary" for p in parts[1:])
                ch = get_or_create(session, Character, nm)
                if faction_obj and ch and ch.faction_id is None:
                    ch.faction_id = faction_obj.id
                    session.add(ch); session.commit()
                link = ItemCharacter(item_id=item.id, character_id=ch.id, is_primary=is_primary)
                if is_primary:
                    primary_set = True
                session.add(link)

            if chars and not primary_set:
                first = chars[0].split("|")[0].strip()
                ch = session.exec(select(Character).where(Character.name == first)).first()
                if ch:
                    link = session.exec(select(ItemCharacter).where(ItemCharacter.item_id == item.id, ItemCharacter.character_id == ch.id)).first()
                    if link:
                        link.is_primary = True

            # purchase
            vendor = get_or_create(session, Vendor, get("vendor"))
            price = to_float(get("price") or "")
            tax = to_float(get("tax") or "")
            shipping = to_float(get("shipping") or "")
            currency = (get("currency") or None)
            order_number = (get("order_number") or None)
            order_date = None
            order_raw = get("order_date")
            if order_raw:
                order_date = parse_date(order_raw)

            purchase_date = None
            pd_raw = get("purchase_date")
            if pd_raw:
                purchase_date = parse_date(pd_raw)

            ship_date = None
            ship_raw = get("ship_date")
            if ship_raw:
                ship_date = parse_date(ship_raw)

            effective_order_date = order_date or purchase_date

            if any([vendor, price, tax, shipping, currency, order_number, effective_order_date, ship_date]):
                p = Purchase(
                    item_id=item.id,
                    vendor_id=vendor.id if vendor else None,
                    price=price,
                    tax=tax,
                    shipping=shipping,
                    currency=currency,
                    order_number=order_number,
                    order_date=effective_order_date,
                    purchase_date=purchase_date,
                    ship_date=ship_date,
                )
                session.add(p)

            session.commit()
            count += 1

        print(f"Imported {count} items.")

if __name__ == "__main__":
    main()
