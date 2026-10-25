"""Seul point d'entrée pour modifier le stock. Atomique, verrouillé et contrôlé côté serveur."""
from django.core.exceptions import PermissionDenied
from django.db import transaction

from catalog.models import Product
from core.audit import log_action
from core.models import Status

from .models import MovementType, StockMovement

SIGN = {
    MovementType.IN: 1, MovementType.OUT: -1,
    MovementType.ADJUST_PLUS: 1, MovementType.ADJUST_MINUS: -1,
}
ADJUSTMENTS = {MovementType.ADJUST_PLUS, MovementType.ADJUST_MINUS}
OPPOSITE = {
    MovementType.IN: MovementType.OUT, MovementType.OUT: MovementType.IN,
    MovementType.ADJUST_PLUS: MovementType.ADJUST_MINUS, MovementType.ADJUST_MINUS: MovementType.ADJUST_PLUS,
}


class StockError(Exception):
    """Opération de stock invalide."""


class InsufficientStock(StockError):
    """Le stock deviendrait négatif."""


def _require_perm(user, perm):
    if user is None or not user.is_active or not user.has_perm(perm):
        raise PermissionDenied(f"Permission requise : {perm}")


@transaction.atomic
def record_movement(*, product, movement_type, quantity, user, reason="", reference="", reverses=None):
    movement_type = MovementType(movement_type)
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise StockError("La quantité doit être un entier strictement positif.")
    is_adjustment = movement_type in ADJUSTMENTS
    _require_perm(user, "inventory.adjust_stock" if is_adjustment else "inventory.add_stockmovement")
    reason = (reason or "").strip()
    if is_adjustment and not reason:
        raise StockError("Un motif est obligatoire pour un ajustement.")

    locked = Product.objects.select_for_update().get(pk=product.pk)  # verrou de ligne
    if locked.status == Status.ARCHIVED:
        raise StockError("Produit archivé : aucun mouvement possible.")
    before = locked.quantity
    after = before + SIGN[movement_type] * quantity
    if after < 0:
        raise InsufficientStock(f"Stock insuffisant : {before} disponible(s), {quantity} demandé(s).")

    movement = StockMovement.objects.create(
        product=locked, movement_type=movement_type, quantity=quantity,
        quantity_before=before, quantity_after=after, created_by=user,
        reason=reason, reference=(reference or "").strip(), reverses=reverses,
    )
    locked.quantity = after
    locked.save(update_fields=["quantity", "updated_at"])
    product.quantity = after  # garde l'instance de l'appelant à jour

    if is_adjustment or reverses is not None:
        log_action(user, "stock.reversal" if reverses else "stock.adjustment", movement,
                   product_id=locked.pk, type=movement_type.value, quantity=quantity, reason=reason)
    return movement


@transaction.atomic
def reverse_movement(*, movement, user, reason):
    """Annule un mouvement par un mouvement inverse. L'original est conservé."""
    _require_perm(user, "inventory.adjust_stock")
    if movement.reverses_id is not None:
        raise StockError("Un mouvement d'annulation ne peut pas être annulé.")
    if hasattr(movement, "reversed_by"):
        raise StockError("Ce mouvement a déjà été annulé.")
    if not (reason or "").strip():
        raise StockError("Un motif est obligatoire pour une annulation.")
    return record_movement(
        product=movement.product, movement_type=OPPOSITE[MovementType(movement.movement_type)],
        quantity=movement.quantity, user=user, reason=reason,
        reference=f"annulation #{movement.pk}", reverses=movement,
    )
