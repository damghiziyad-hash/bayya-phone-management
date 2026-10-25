from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from core.i18n import localized
from core.models import Status, TimeStampedModel

ZERO = Decimal("0")


class Category(TimeStampedModel):
    name_fr = models.CharField(_("nom (français)"), max_length=100, unique=True)
    name_ar = models.CharField(_("nom (arabe)"), max_length=100, blank=True)
    description = models.TextField(_("description"), blank=True)
    status = models.CharField(_("statut"), max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["name_fr"]
        verbose_name = _("catégorie")
        verbose_name_plural = _("catégories")

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return localized(self.name_fr, self.name_ar)


class StockStatus:
    NORMAL = "normal"
    LOW = "low"
    OUT = "out"
    ARCHIVED = "archived"


class Product(TimeStampedModel):
    sku = models.CharField(_("référence (SKU)"), max_length=64, unique=True)
    barcode = models.CharField(_("code-barres"), max_length=64, blank=True)
    name_fr = models.CharField(_("nom (français)"), max_length=200)
    name_ar = models.CharField(_("nom (arabe)"), max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name=_("catégorie"))
    phone_brand = models.CharField(_("marque compatible"), max_length=100, blank=True)
    phone_model = models.CharField(_("modèle compatible"), max_length=100, blank=True)
    purchase_price = models.DecimalField(_("prix d'achat"), max_digits=12, decimal_places=2,
                                         default=ZERO, validators=[MinValueValidator(ZERO)])
    sale_price = models.DecimalField(_("prix de vente"), max_digits=12, decimal_places=2,
                                     default=ZERO, validators=[MinValueValidator(ZERO)])
    # Modifié UNIQUEMENT par inventory.services.record_movement (jamais directement).
    quantity = models.PositiveIntegerField(_("quantité en stock"), default=0)
    low_stock_threshold = models.PositiveIntegerField(_("seuil d'alerte"), default=5)  # hypothèse : 5
    location = models.CharField(_("emplacement"), max_length=100, blank=True)
    status = models.CharField(_("statut"), max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["name_fr"]
        verbose_name = _("produit")
        verbose_name_plural = _("produits")
        permissions = [("view_purchase_price", "Peut voir le prix d'achat")]
        constraints = [
            models.CheckConstraint(condition=Q(purchase_price__gte=0), name="product_purchase_price_gte_0"),
            models.CheckConstraint(condition=Q(sale_price__gte=0), name="product_sale_price_gte_0"),
            models.UniqueConstraint(fields=["barcode"], condition=~Q(barcode=""), name="product_barcode_unique_if_set"),
        ]
        indexes = [
            models.Index(fields=["name_fr"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["phone_brand", "phone_model"]),
        ]

    def __str__(self):
        return f"{self.sku} — {self.display_name}"

    def save(self, *args, **kwargs):
        self.sku = (self.sku or "").strip().upper()
        self.barcode = (self.barcode or "").strip()
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return localized(self.name_fr, self.name_ar)

    @property
    def stock_status(self):
        if self.status == Status.ARCHIVED:
            return StockStatus.ARCHIVED
        if self.quantity == 0:
            return StockStatus.OUT
        if self.quantity <= self.low_stock_threshold:
            return StockStatus.LOW
        return StockStatus.NORMAL
