from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from core.exceptions import ImmutableRecordError


class MovementType(models.TextChoices):
    IN = "in", _("Entrée")
    OUT = "out", _("Sortie")
    ADJUST_PLUS = "adjust_plus", _("Ajustement positif")
    ADJUST_MINUS = "adjust_minus", _("Ajustement négatif")


class StockMovementQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ImmutableRecordError("Les mouvements de stock ne peuvent pas être modifiés.")

    def delete(self):
        raise ImmutableRecordError("Les mouvements de stock ne peuvent pas être supprimés.")


class StockMovement(models.Model):
    """Mouvement en ajout seul. Une erreur se corrige par un mouvement compensatoire (`reverses`)."""

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.PositiveIntegerField(_("quantité"))
    quantity_before = models.PositiveIntegerField()
    quantity_after = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_movements")
    reason = models.CharField(_("motif"), max_length=255, blank=True)
    reference = models.CharField(_("référence"), max_length=100, blank=True)
    reverses = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversed_by")

    objects = StockMovementQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        default_permissions = ("add", "view")
        permissions = [("adjust_stock", "Peut corriger le stock (ajustements, annulations)")]
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name="stockmovement_quantity_gt_0")]
        indexes = [models.Index(fields=["product", "-created_at"])]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} × {self.product_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableRecordError("Un mouvement de stock ne peut pas être modifié.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableRecordError("Un mouvement de stock ne peut pas être supprimé.")
