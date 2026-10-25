
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Customer


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        label=_("Nom complet"),
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Votre nom complet",
            "autocomplete": "name",
        }),
    )

    phone = forms.CharField(
        label=_("Téléphone"),
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Votre numéro de téléphone",
            "type": "tel",
            "autocomplete": "tel",
        }),
    )

    city = forms.CharField(
        label=_("Ville"),
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Votre ville",
            "autocomplete": "address-level2",
        }),
    )

    address = forms.CharField(
        label=_("Adresse"),
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Votre adresse complète",
            "rows": 3,
            "autocomplete": "street-address",
        }),
    )

    email = forms.EmailField(
        label=_("Email (facultatif)"),
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "exemple@email.com",
            "autocomplete": "email",
        }),
    )

    quantity = forms.IntegerField(
        label=_("Quantité"),
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": 1,
        }),
    )
