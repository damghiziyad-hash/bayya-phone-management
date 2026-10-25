"""Calcul des indicateurs du tableau de bord (séparé des vues pour être testable)."""
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce

from catalog.models import Product
from core.models import Status
from inventory.models import StockMovement

WATCH_LIMIT = 10
RECENT_LIMIT = 10
MONEY = DecimalField(max_digits=18, decimal_places=2)


def get_dashboard_stats(user):
    """Indicateurs de stock. Les produits archivés sont exclus de tous les calculs.

    - stock_value n'est calculée que si l'utilisateur a `catalog.view_purchase_price`.
    - recent_movements n'est chargé que si l'utilisateur a `inventory.view_stockmovement`.
    (None = « non autorisé », différent de 0 ou d'une liste vide.)
    """
    active = Product.objects.filter(status=Status.ACTIVE)

    totals = active.aggregate(
        active_count=Count("pk"),
        total_quantity=Coalesce(Sum("quantity"), Value(0)),
    )
    out_count = active.filter(quantity=0).count()
    low_count = active.filter(quantity__gt=0, quantity__lte=F("low_stock_threshold")).count()
    watch_list = list(
        active.filter(quantity__lte=F("low_stock_threshold"))
        .select_related("category")
        .order_by("quantity", "name_fr")[:WATCH_LIMIT]
    )

    stock_value = None
    if user.has_perm("catalog.view_purchase_price"):
        line_value = ExpressionWrapper(F("quantity") * F("purchase_price"), output_field=MONEY)
        stock_value = active.aggregate(
            v=Coalesce(Sum(line_value), Value(Decimal("0.00")), output_field=MONEY)
        )["v"]

    recent_movements = None
    if user.has_perm("inventory.view_stockmovement"):
        recent_movements = list(
            StockMovement.objects.select_related("product", "created_by")[:RECENT_LIMIT]
        )

    return {
        "active_count": totals["active_count"],
        "total_quantity": totals["total_quantity"],
        "low_count": low_count,
        "out_count": out_count,
        "watch_list": watch_list,
        "stock_value": stock_value,
        "recent_movements": recent_movements,
    }
