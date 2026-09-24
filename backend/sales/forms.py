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
        if not isinstance(field, forms.ModelChoiceField):
            return

        allowed = Q(is_active=True)
        current = self.instance.product_id
        if current:
            allowed |= Q(pk=current)
        field.queryset = Product.objects.filter(allowed)
