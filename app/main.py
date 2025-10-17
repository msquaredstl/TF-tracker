from collections import Counter, defaultdict
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from .db.session import init_db, get_session
from .models import (
    Category,
    Character,
    Company,
    Item,
    ItemCharacter,
    ItemType,
    Line,
    Purchase,
    Series,
)
from .utils import get_or_create, split_characters

app = FastAPI(title="Transformers Collection Tracker — Complete")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: Optional[str] = None, status: Optional[str] = None, company: Optional[str] = None, session: Session = Depends(get_session)):
    stmt = select(Item)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Item.name.ilike(like) | Item.sku.ilike(like) | Item.notes.ilike(like))
    if status:
        stmt = stmt.where(Item.status == status)
    if company:
        c = session.exec(select(Company).where(Company.name == company)).first()
        if c:
            stmt = stmt.where(Item.company_id == c.id)
    items = session.exec(stmt.order_by(Item.name.asc())).all()

    companies = session.exec(select(Company.name)).all()
    companies = sorted(set([c for c in companies if c]))
    return templates.TemplateResponse("items_list.html", {"request": request, "items": items, "q": q or "", "status": status or "", "companies": companies, "active_company": company or ""})


@app.get("/imports", response_class=HTMLResponse)
def imported_items(request: Request, session: Session = Depends(get_session)):
    items = session.exec(select(Item).order_by(Item.name.asc())).all()
    return templates.TemplateResponse(
        "imported_items.html", {"request": request, "items": items}
    )


@app.get("/collection", response_class=HTMLResponse)
def collection_overview(
    request: Request,
    owner: Optional[str] = None,
    session: Session = Depends(get_session),
):
    stmt = (
        select(Item)
        .options(
            selectinload(Item.company),
            selectinload(Item.purchases).selectinload(Purchase.vendor),
        )
        .order_by(Item.name.asc())
    )
    items = session.exec(stmt).unique().all()

    item_rows: List[Dict[str, Optional[str]]] = []
    status_counter: Counter[str] = Counter()
    company_counter: Counter[str] = Counter()
    currency_totals = defaultdict(float)

    for item in items:
        owner_id = None
        if isinstance(item.extra, dict):
            owner_raw = item.extra.get("owner_id")
            if owner_raw is not None:
                owner_id = str(owner_raw)

        if owner and owner_id != owner:
            continue

        company_name = item.company.name if item.company else "Unbranded"
        status_value = item.status or "Unknown"
        status_counter[status_value] += 1
        company_counter[company_name] += 1

        primary_purchase = item.purchases[0] if item.purchases else None
        price_display = ""
        purchase_date = ""
        vendor_name = ""
        if primary_purchase:
            purchase_date = (
                primary_purchase.purchase_date.isoformat()
                if primary_purchase.purchase_date
                else ""
            )
            vendor_name = primary_purchase.vendor.name if primary_purchase.vendor else ""
            if primary_purchase.price is not None:
                currency = primary_purchase.currency or "USD"
                price_display = f"{currency} {primary_purchase.price:0.2f}"

        for purchase in item.purchases:
            if purchase.price is None:
                continue
            currency = purchase.currency or "USD"
            currency_totals[currency] += purchase.price

        item_rows.append(
            {
                "id": str(item.id) if item.id is not None else "",
                "name": item.name,
                "company": company_name,
                "status": status_value,
                "purchase_date": purchase_date,
                "vendor": vendor_name,
                "price": price_display,
                "owner": owner_id or "—",
            }
        )

    status_breakdown = sorted(
        status_counter.items(), key=lambda pair: (-pair[1], pair[0])
    )
    company_breakdown = sorted(
        company_counter.items(), key=lambda pair: (-pair[1], pair[0])
    )
    currency_breakdown = [
        (currency, total)
        for currency, total in sorted(currency_totals.items(), key=lambda pair: pair[0])
    ]

    return templates.TemplateResponse(
        "collection_overview.html",
        {
            "request": request,
            "owner": owner,
            "item_rows": item_rows,
            "total_items": len(item_rows),
            "status_breakdown": status_breakdown,
            "company_breakdown": company_breakdown,
            "currency_breakdown": currency_breakdown,
        },
    )

@app.get("/items/new", response_class=HTMLResponse)
def new_item_form(request: Request):
    return templates.TemplateResponse("item_form.html", {"request": request, "item": None})

def _sync_characters(session: Session, item: Item, characters_csv: Optional[str]):
    for link in list(item.character_links):
        session.delete(link)
    if not characters_csv:
        return
    entries = split_characters(characters_csv)
    primary_set = False
    for idx, e in enumerate(entries):
        name = e
        is_primary = False
        if "|" in e:
            parts = [p.strip() for p in e.split("|")]
            name = parts[0]
            is_primary = any(p.lower() == "primary" for p in parts[1:])
        ch = get_or_create(session, Character, name)
        link = ItemCharacter(item_id=item.id, character_id=ch.id, is_primary=is_primary)
        if is_primary:
            primary_set = True
        session.add(link)
    if entries and not primary_set:
        first = entries[0].split("|")[0].strip()
        ch = session.exec(select(Character).where(Character.name == first)).first()
        if ch:
            link = session.exec(select(ItemCharacter).where(ItemCharacter.item_id == item.id, ItemCharacter.character_id == ch.id)).first()
            if link:
                link.is_primary = True

@app.post("/items/new")
def create_item(
    name: str = Form(...),
    sku: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    scale: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    status: Optional[str] = Form("Owned"),
    location: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    line_name: Optional[str] = Form(None),
    series_name: Optional[str] = Form(None),
    type_name: Optional[str] = Form(None),
    category_name: Optional[str] = Form(None),
    characters: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    item = Item(
        name=name, sku=sku, version=version, year=year, scale=scale, condition=condition,
        status=status, location=location, url=url, notes=notes
    )
    company = get_or_create(session, Company, company_name)
    if company: item.company_id = company.id
    line = get_or_create(session, Line, line_name)
    if line:
        if company and line.company_id is None:
            line.company_id = company.id
            session.add(line); session.commit()
        item.line_id = line.id
    series = get_or_create(session, Series, series_name)
    if series: item.series_id = series.id
    type_ = get_or_create(session, ItemType, type_name)
    if type_: item.type_id = type_.id
    category = get_or_create(session, Category, category_name)
    if category: item.category_id = category.id

    session.add(item); session.commit(); session.refresh(item)
    _sync_characters(session, item, characters)
    session.commit()
    return RedirectResponse(url=f"/items/{item.id}", status_code=303)

@app.get("/items/{item_id}", response_class=HTMLResponse)
def item_detail(request: Request, item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        return RedirectResponse(url="/", status_code=303)
    names: List[str] = []
    for l in item.character_links:
        names.append(f"{l.character.name}{' |primary' if l.is_primary else ''}")
    characters_csv = ", ".join(names)
    return templates.TemplateResponse("item_detail.html", {"request": request, "item": item, "characters_csv": characters_csv})

@app.post("/items/{item_id}/edit")
def update_item(
    item_id: int,
    name: str = Form(...),
    sku: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    scale: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    status: Optional[str] = Form("Owned"),
    location: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    line_name: Optional[str] = Form(None),
    series_name: Optional[str] = Form(None),
    type_name: Optional[str] = Form(None),
    category_name: Optional[str] = Form(None),
    characters: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    item = session.get(Item, item_id)
    if not item:
        return RedirectResponse(url="/", status_code=303)

    item.name, item.sku, item.version = name, sku, version
    item.year, item.scale, item.condition = year, scale, condition
    item.status, item.location, item.url, item.notes = status, location, url, notes

    company = get_or_create(session, Company, company_name)
    item.company_id = company.id if company else None

    line = get_or_create(session, Line, line_name)
    if line:
        if company and line.company_id is None:
            line.company_id = company.id
            session.add(line); session.commit()
        item.line_id = line.id
    else:
        item.line_id = None

    series = get_or_create(session, Series, series_name)
    item.series_id = series.id if series else None

    type_ = get_or_create(session, ItemType, type_name)
    item.type_id = type_.id if type_ else None

    category = get_or_create(session, Category, category_name)
    item.category_id = category.id if category else None

    session.add(item); session.commit()
    _sync_characters(session, item, characters)
    session.commit()
    return RedirectResponse(url=f"/items/{item.id}", status_code=303)

@app.post("/items/{item_id}/delete")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if item:
        session.delete(item)
        session.commit()
    return RedirectResponse(url="/", status_code=303)
