from django import forms
from django.utils.translation import gettext_lazy as _

from catalog.models import Product
from core.models import Status


class StockInForm(forms.Form):
    product = forms.ModelChoiceField(
        label=_("Produit"),
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.IntegerField(
        label=_("Quantité reçue"),
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )
    supplier = forms.CharField(
        label=_("Fournisseur"),
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    reference = forms.CharField(
        label=_("Référence de facture"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    note = forms.CharField(
        label=_("Note"),
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = (
            Product.objects.filter(status=Status.ACTIVE)
            .select_related("category")
            .order_by("name_fr")
        )
        self.fields["product"].label_from_instance = (
            lambda product: f"{product.sku} — {product.display_name}"
        )
