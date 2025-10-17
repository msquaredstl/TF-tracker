"""Views powering the Django web frontend."""
from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ITEM_STATUS_CHOICES, ItemForm
from .models import (
    Category,
    Character,
    Company,
    Item,
    ItemCharacter,
    ItemType,
    Line,
    Series,
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


def _sync_characters(item: Item, characters_raw: str | None) -> None:
    item.character_links.all().delete()
    entries = _split_characters(characters_raw)
    created_links: List[ItemCharacter] = []
    primary_found = False
    for entry in entries:
        parts = [part.strip() for part in entry.split("|")]
        name = parts[0]
        is_primary = any(part.lower() == "primary" for part in parts[1:])
        character, _ = Character.objects.get_or_create(name=name)
        link = ItemCharacter.objects.create(
            item=item,
            character=character,
            is_primary=is_primary,
        )
        created_links.append(link)
        if is_primary:
            primary_found = True
    if entries and not primary_found and created_links:
        first_link = created_links[0]
        first_link.is_primary = True
        first_link.save(update_fields=["is_primary"])


def _initial_data_for_item(item: Item | None) -> dict[str, object]:
    if not item:
        return {"status": "Owned"}
    characters: Iterable[str] = []
    if item:
        characters = [
            f"{link.character.name}{' |primary' if link.is_primary else ''}"
            for link in item.character_links.select_related("character")
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
    queryset = Item.objects.select_related("company", "line", "series", "type", "category")

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

    items = queryset.order_by("name")

    companies = (
        Company.objects.filter(items__isnull=False)
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
    }
    return render(request, "tracker/item_list.html", context)


def item_detail(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(
        Item.objects.select_related("company", "line", "series", "type", "category"), pk=pk
    )
    characters = [
        {
            "name": link.character.name,
            "is_primary": link.is_primary,
        }
        for link in item.character_links.select_related("character").all()
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
