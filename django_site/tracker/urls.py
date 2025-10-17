from __future__ import annotations

from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.item_list, name="item-list"),
    path("items/<int:pk>/", views.item_detail, name="item-detail"),
    path("items/new/", views.item_create, name="item-create"),
    path("items/<int:pk>/edit/", views.item_edit, name="item-edit"),
    path("items/<int:pk>/delete/", views.item_delete, name="item-delete"),
]
