from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Category, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "sku",
            "barcode",
            "name_fr",
            "name_ar",
            "image",
            "category",
            "phone_brand",
            "phone_model",
            "purchase_price",
            "sale_price",
            "low_stock_threshold",
            "location",
            "status",
        ]
        widgets = {
            "sku": forms.TextInput(attrs={"class": "form-control"}),
            "barcode": forms.TextInput(attrs={"class": "form-control"}),
            "name_fr": forms.TextInput(attrs={"class": "form-control"}),
            "name_ar": forms.TextInput(attrs={"class": "form-control", "dir": "rtl"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "phone_brand": forms.TextInput(attrs={"class": "form-control"}),
            "phone_model": forms.TextInput(attrs={"class": "form-control"}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }
        labels = {
            "sku": _("Référence (SKU)"),
            "barcode": _("Code-barres"),
            "name_fr": _("Nom en français"),
            "name_ar": _("Nom en arabe"),
            "category": _("Catégorie"),
            "phone_brand": _("Marque compatible"),
            "phone_model": _("Modèle compatible"),
            "purchase_price": _("Prix d'achat"),
            "sale_price": _("Prix de vente"),
            "low_stock_threshold": _("Seuil d'alerte"),
            "location": _("Emplacement"),
            "status": _("Statut"),
            "image": _("Photo du produit"),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.all()

        # Le prix d'achat ne doit pas être accessible sans permission.
        if user is None or not user.has_perm("catalog.view_purchase_price"):
            self.fields.pop("purchase_price", None)

        # La quantité n'est volontairement pas dans ce formulaire.
