
"""Services métier pour la gestion des commandes."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.models import Role
from catalog.models import Product
from inventory.models import MovementType
from inventory.services import (
    InsufficientStock,
    StockError,
    record_movement,
)

from .models import Order


@transaction.atomic
def confirm_order(*, order_id, user):
    """Confirme une commande et déduit le stock une seule fois."""

    if (
        user is None
        or not user.is_authenticated
        or not user.is_active
        or user.role not in (Role.OWNER, Role.STOCK_MANAGER)
    ):
        raise PermissionDenied(
            "Vous n'avez pas le droit de confirmer cette commande."
        )

    # La sortie de stock nécessite aussi cette permission.
    if not user.has_perm("inventory.add_stockmovement"):
        raise PermissionDenied(
            "Permission manquante : inventory.add_stockmovement"
        )

    # Verrouiller la commande empêche une double confirmation concurrente.
    order = (
        Order.objects.select_for_update()
        .select_related("customer")
        .get(pk=order_id)
    )

    if order.status != Order.Status.PENDING:
        raise ValidationError(
            "Seules les commandes en attente peuvent être confirmées."
        )

    items = list(
        order.items.select_related("product").order_by("product_id", "id")
    )

    if not items:
        raise ValidationError("Impossible de confirmer une commande vide.")

    # Vérifier tout le stock avant de commencer les mouvements.
    product_ids = sorted({item.product_id for item in items})
    locked_products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .order_by("pk")
    }

    required = {}
    for item in items:
        required[item.product_id] = (
            required.get(item.product_id, 0) + item.quantity
        )

    for product_id, quantity in required.items():
        product = locked_products.get(product_id)
        if product is None:
            raise ValidationError("Un produit de la commande n'existe plus.")
        if product.quantity < quantity:
            raise InsufficientStock(
                f"Stock insuffisant pour {product.display_name} : "
                f"{product.quantity} disponible(s), {quantity} demandé(s)."
            )

    # Enregistrer le coût d'achat au moment de la confirmation.
    for item in items:
        product = locked_products[item.product_id]
        item.purchase_unit_cost = product.purchase_price
        item.save(update_fields=["purchase_unit_cost"])

    # Déduire le stock uniquement via le service officiel.
    for product_id, quantity in required.items():
        product = locked_products[product_id]
        record_movement(
            product=product,
            movement_type=MovementType.OUT,
            quantity=quantity,
            user=user,
            reason="Commande confirmée",
            reference=f"Commande #{order.pk}",
        )

    order.status = Order.Status.CONFIRMED
    order.save(update_fields=["status", "updated_at"])

    return order
