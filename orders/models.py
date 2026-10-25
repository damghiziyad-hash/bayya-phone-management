
from django.db import models
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    full_name = models.CharField(_("Nom complet"), max_length=150)
    phone = models.CharField(_("Téléphone"), max_length=30)
    city = models.CharField(_("Ville"), max_length=100)
    address = models.TextField(_("Adresse"))
    email = models.EmailField(_("Email"), blank=True)

    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return f"{self.full_name} — {self.phone}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        CONFIRMED = "confirmed", _("Confirmée")
        PREPARING = "preparing", _("En préparation")
        SHIPPED = "shipped", _("Expédiée")
        DELIVERED = "delivered", _("Livrée")
        CANCELLED = "cancelled", _("Annulée")
        UNREACHABLE = "unreachable", _("Client injoignable")

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("Client"),
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(_("Date de commande"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Dernière modification"), auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")

    def __str__(self):
        return f"Commande #{self.pk} — {self.customer.full_name}"

    @property
    def total(self):
        return sum(item.line_total for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Commande"),
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name=_("Produit"),
    )
    product_name = models.CharField(
        _("Nom du produit"),
        max_length=200,
    )

    unit_price = models.DecimalField(
        _("Prix unitaire au moment de la commande"),
        max_digits=12,
        decimal_places=2,
    )

    purchase_unit_cost = models.DecimalField(
        _("Coût d'achat unitaire au moment de la confirmation"),
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    quantity = models.PositiveIntegerField(_("Quantité"))

    class Meta:
        verbose_name = _("Ligne de commande")
        verbose_name_plural = _("Lignes de commande")

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
    @property
    def cost_total(self):
        """Coût d'achat total enregistré à la confirmation."""
        return self.purchase_unit_cost * self.quantity

    @property
    def profit(self):
        """Marge estimée pour cette ligne de commande."""
        return self.line_total - self.cost_total
