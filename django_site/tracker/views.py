"""Views powering the Django web frontend."""
from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from django.db import connection, transaction
from django.db.models import Min, Q
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ITEM_STATUS_CHOICES, ItemForm
from .models import (
    Category,
    Character,
    Company,
    Faction,
    Item,
    ItemType,
    Line,
    Series,
    Team,
    Vendor,
)


def _clean_name(value: str | None) -> str | None:
    if not value:
        return None
    name = value.strip()
    return name or None


def _get_or_create_company(name: str | None) -> Company | None:
    cleaned = _clean_name(name)
    if not cleaned:
        return None
    company, _ = Company.objects.get_or_create(name=cleaned)
    return company


def _get_or_create_line(name: str | None, company: Company | None) -> Line | None:
    cleaned = _clean_name(name)
    if not cleaned:
        return None
    line, _ = Line.objects.get_or_create(name=cleaned)
    if company and line.company_id is None:
        line.company = company
        line.save(update_fields=["company"])
    return line


def _get_or_create_by_name(model, name: str | None):
    cleaned = _clean_name(name)
    if not cleaned:
        return None
    obj, _ = model.objects.get_or_create(name=cleaned)
    return obj


def _split_characters(value: str | None) -> List[str]:
    if not value:
        return []
    tokens = value.replace(";", "\n").replace(",", "\n").splitlines()
    entries: List[str] = []
    for raw in tokens:
        token = raw.strip()
        if not token:
            continue
        if "|" in token:
            parts = [part.strip() for part in token.split("|")]
            head = parts[0]
            tail = [part for part in parts[1:] if part]
            token = head
            if tail:
                token = head + " |" + " |".join(tail)
        entries.append(token)
    return entries


def _normalize_character_tokens(value: str | None) -> List[str]:
    tokens: List[str] = []
    for entry in _split_characters(value):
        head = entry.split("|")[0].strip()
        if head and head not in tokens:
            tokens.append(head)
    return tokens


def _parse_date_filter(value: str | None):
    if not value:
        return None
    parsed = parse_date(value)
    return parsed


def _sync_characters(item: Item, characters_raw: str | None) -> None:
    entries = _split_characters(characters_raw)
    primary_found = False
    first_character_id: int | None = None
    seen_character_ids: set[int] = set()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM itemcharacter WHERE item_id = %s", [item.pk])
        for entry in entries:
            parts = [part.strip() for part in entry.split("|") if part.strip()]
            if not parts:
                continue
            name = parts[0]
            is_primary = any(part.lower() == "primary" for part in parts[1:])
            character, _ = Character.objects.get_or_create(name=name)
            if character.pk in seen_character_ids:
                continue
            seen_character_ids.add(character.pk)
            if first_character_id is None:
                first_character_id = character.pk
            cursor.execute(
                """
                INSERT INTO itemcharacter (item_id, character_id, is_primary, role)
                VALUES (%s, %s, %s, NULL)
                """,
                [item.pk, character.pk, 1 if is_primary else 0],
            )
            if is_primary:
                primary_found = True
        if entries and not primary_found and first_character_id is not None:
            cursor.execute(
                """
                UPDATE itemcharacter
                SET is_primary = 1
                WHERE item_id = %s AND character_id = %s
                """,
                [item.pk, first_character_id],
            )


def _initial_data_for_item(item: Item | None) -> dict[str, object]:
    if not item:
        return {"status": "Owned"}
    characters: Iterable[str] = []
    if item:
        characters = [
            f"{row['name']}{' |primary' if row['is_primary'] else ''}"
            for row in item.character_rows()
        ]
    characters_csv = ", ".join(characters)
    return {
        "name": item.name,
        "sku": item.sku or "",
        "version": item.version or "",
        "year": item.year,
        "scale": item.scale or "",
        "condition": item.condition or "",
        "status": item.status or "Owned",
        "location": item.location or "",
        "url": item.url or "",
        "notes": item.notes or "",
        "company_name": item.company.name if item.company else "",
        "line_name": item.line.name if item.line else "",
        "series_name": item.series.name if item.series else "",
        "type_name": item.type.name if item.type else "",
        "category_name": item.category.name if item.category else "",
        "characters": characters_csv,
    }


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _save_item_from_form(data: Mapping[str, Any], *, instance: Item | None = None) -> Item:
    with transaction.atomic():
        item = instance or Item()
        item.name = _as_optional_str(data.get("name")) or ""
        item.sku = _as_optional_str(data.get("sku"))
        item.version = _as_optional_str(data.get("version"))
        year_value = data.get("year")
        item.year = year_value if isinstance(year_value, int) else None
        item.scale = _as_optional_str(data.get("scale"))
        item.condition = _as_optional_str(data.get("condition"))
        item.status = _as_optional_str(data.get("status")) or "Owned"
        item.location = _as_optional_str(data.get("location"))
        item.url = _as_optional_str(data.get("url"))
        item.notes = _as_optional_str(data.get("notes"))

        company = _get_or_create_company(_as_optional_str(data.get("company_name")))
        line = _get_or_create_line(_as_optional_str(data.get("line_name")), company)
        item.company = company
        item.line = line
        item.series = _get_or_create_by_name(Series, _as_optional_str(data.get("series_name")))
        item.type = _get_or_create_by_name(ItemType, _as_optional_str(data.get("type_name")))
        item.category = _get_or_create_by_name(Category, _as_optional_str(data.get("category_name")))

        item.save()
        _sync_characters(item, _as_optional_str(data.get("characters")))
    return item


def item_list(request: HttpRequest) -> HttpResponse:
    """List items with optional filtering that mirrors the FastAPI frontend."""
    queryset = (
        Item.objects.select_related("company", "line", "series", "type", "category")
        .annotate(
            order_date_value=Coalesce(
                Min("purchases__order_date"),
                Min("purchases__purchase_date"),
            ),
            ship_date_value=Min("purchases__ship_date"),
        )
    )

    query = request.GET.get("q")
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(notes__icontains=query)
        )

    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)

    company_name = request.GET.get("company")
    if company_name:
        queryset = queryset.filter(company__name=company_name)

    line_name = request.GET.get("line")
    if line_name:
        queryset = queryset.filter(line__name=line_name)

    series_name = request.GET.get("series")
    if series_name:
        queryset = queryset.filter(series__name=series_name)

    type_name = request.GET.get("type")
    if type_name:
        queryset = queryset.filter(type__name=type_name)

    category_name = request.GET.get("category")
    if category_name:
        queryset = queryset.filter(category__name=category_name)

    faction_name = request.GET.get("faction")
    if faction_name:
        queryset = queryset.filter(character_links__character__faction__name=faction_name)

    team_name = request.GET.get("team")
    if team_name:
        queryset = queryset.filter(character_links__character__team_links__team__name=team_name)

    vendor_name = request.GET.get("vendor")
    if vendor_name:
        queryset = queryset.filter(purchases__vendor__name=vendor_name)

    characters_value = request.GET.get("characters")
    active_characters = _normalize_character_tokens(characters_value)
    for character_name in active_characters:
        queryset = queryset.filter(character_links__character__name__iexact=character_name)

    order_date_raw = request.GET.get("order_date")
    order_date_value = _parse_date_filter(order_date_raw)
    if order_date_value:
        queryset = queryset.filter(
            Q(purchases__order_date=order_date_value)
            | Q(purchases__purchase_date=order_date_value)
        )

    ship_date_raw = request.GET.get("ship_date")
    ship_date_value = _parse_date_filter(ship_date_raw)
    if ship_date_value:
        queryset = queryset.filter(purchases__ship_date=ship_date_value)

    queryset = queryset.distinct()

    order_sort = request.GET.get("order_sort")
    ship_sort = request.GET.get("ship_sort")

    order_by_fields: List[str] = []
    if order_sort in {"asc", "desc"}:
        field = "order_date_value"
        if order_sort == "desc":
            field = f"-{field}"
        order_by_fields.append(field)
    if ship_sort in {"asc", "desc"}:
        field = "ship_date_value"
        if ship_sort == "desc":
            field = f"-{field}"
        order_by_fields.append(field)
    order_by_fields.append("name")

    items = queryset.order_by(*order_by_fields)

    companies = (
        Company.objects.filter(items__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    lines = (
        Line.objects.filter(items__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    series_options = (
        Series.objects.filter(items__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    types = (
        ItemType.objects.filter(items__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    categories = (
        Category.objects.filter(items__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    factions = (
        Faction.objects.filter(characters__item_links__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    teams = (
        Team.objects.filter(character_links__character__item_links__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    vendors = (
        Vendor.objects.filter(purchases__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    character_options = (
        Character.objects.filter(item_links__isnull=False)
        .order_by("name")
        .values_list("name", flat=True)
        .distinct()
    )

    context = {
        "items": items,
        "query": query or "",
        "status": status or "",
        "status_choices": ITEM_STATUS_CHOICES,
        "companies": companies,
        "active_company": company_name or "",
        "lines": lines,
        "active_line": line_name or "",
        "series_options": series_options,
        "active_series": series_name or "",
        "types": types,
        "active_type": type_name or "",
        "categories": categories,
        "active_category": category_name or "",
        "factions": factions,
        "active_faction": faction_name or "",
        "teams": teams,
        "active_team": team_name or "",
        "vendors": vendors,
        "active_vendor": vendor_name or "",
        "character_options": character_options,
        "active_characters": active_characters,
        "characters_csv": ", ".join(active_characters),
        "order_date": order_date_raw or "",
        "ship_date": ship_date_raw or "",
        "order_sort": order_sort or "",
        "ship_sort": ship_sort or "",
        "order_sort_choices": (
            ("", "Default"),
            ("asc", "Oldest first"),
            ("desc", "Newest first"),
        ),
        "ship_sort_choices": (
            ("", "Default"),
            ("asc", "Earliest ship first"),
            ("desc", "Latest ship first"),
        ),
    }
    return render(request, "tracker/item_list.html", context)


def item_detail(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(
        Item.objects.select_related("company", "line", "series", "type", "category"), pk=pk
    )
    characters = [
        {"name": row["name"], "is_primary": row["is_primary"]}
        for row in item.character_rows()
    ]
    context = {
        "item": item,
        "characters": characters,
    }
    return render(request, "tracker/item_detail.html", context)


def item_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = _save_item_from_form(form.cleaned_data)
            return redirect("tracker:item-detail", pk=item.pk)
    else:
        form = ItemForm(initial=_initial_data_for_item(None))
    context = {
        "form": form,
        "item": None,
        "form_action": reverse("tracker:item-create"),
    }
    return render(request, "tracker/item_form.html", context)


def item_edit(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(Item, pk=pk)
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = _save_item_from_form(form.cleaned_data, instance=item)
            return redirect("tracker:item-detail", pk=item.pk)
    else:
        form = ItemForm(initial=_initial_data_for_item(item))
    context = {
        "form": form,
        "item": item,
        "form_action": reverse("tracker:item-edit", args=[item.pk]),
    }
    return render(request, "tracker/item_form.html", context)


def item_delete(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("tracker:item-detail", pk=pk)
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    return redirect("tracker:item-list")
