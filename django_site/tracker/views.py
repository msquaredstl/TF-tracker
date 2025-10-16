"""Views powering the Django web frontend."""
from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Company, Item


def item_list(request):  # type: ignore[no-untyped-def]
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
        "companies": companies,
        "active_company": company_name or "",
    }
    return render(request, "tracker/item_list.html", context)


def item_detail(request, pk: int):  # type: ignore[no-untyped-def]
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
