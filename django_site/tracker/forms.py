"""Forms backing create/update operations in the Django frontend."""
from __future__ import annotations

from django import forms

STATUS_CHOICES = [
    ("Owned", "Owned"),
    ("Preorder", "Preorder"),
    ("Sold", "Sold"),
    ("Wishlist", "Wishlist"),
]

ITEM_STATUS_CHOICES = [choice[0] for choice in STATUS_CHOICES]


class ItemForm(forms.Form):
    """Form that mirrors the fields available in the FastAPI UI."""

    name = forms.CharField(max_length=255)
    sku = forms.CharField(max_length=255, required=False)
    version = forms.CharField(max_length=255, required=False)
    year = forms.IntegerField(required=False)
    scale = forms.CharField(max_length=255, required=False)
    condition = forms.CharField(max_length=255, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, initial="Owned")
    location = forms.CharField(max_length=255, required=False)
    url = forms.URLField(required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    company_name = forms.CharField(max_length=255, required=False)
    line_name = forms.CharField(max_length=255, required=False)
    series_name = forms.CharField(max_length=255, required=False)
    type_name = forms.CharField(max_length=255, required=False)
    category_name = forms.CharField(max_length=255, required=False)
    characters = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css}"
            if not isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("autocomplete", "off")
        self.fields["characters"].widget.attrs.setdefault(
            "placeholder",
            "Optimus Prime, Megatron |primary",
        )
