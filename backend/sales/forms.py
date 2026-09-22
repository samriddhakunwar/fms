"""
sales/forms.py
==============
Admin form for SaleItem.

Products are retired with ``is_active=False`` rather than deleted (their
SaleItem rows are PROTECTed so the sales audit trail survives). New line
items must therefore only offer active products — but an invoice recorded
before a product was retired still has to be editable, so the product
already stored on the row stays a valid choice for that row.
"""

from django import forms
from django.db.models import Q

from inventory.models import Product

from .models import SaleItem


class SaleItemAdminForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get("product")
        if field is None:
            return

        allowed = Q(is_active=True)
        current = self.instance.product_id
        if current:
            # Keep the already-saved product selectable so editing an old
            # invoice does not fail with "Select a valid choice".
            allowed |= Q(pk=current)
        field.queryset = Product.objects.filter(allowed)
