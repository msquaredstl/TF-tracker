from __future__ import annotations

from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.item_list, name="item-list"),
    path("items/<int:pk>/", views.item_detail, name="item-detail"),
]
