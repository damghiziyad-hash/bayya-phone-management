"""Matrice rôles -> permissions (app_label, codename). Le propriétaire reçoit toutes les permissions."""
from .models import Role

STOCK_MANAGER_PERMS = [
    ("catalog", "view_category"), ("catalog", "add_category"), ("catalog", "change_category"),
    ("catalog", "view_product"), ("catalog", "add_product"), ("catalog", "change_product"),
    ("catalog", "view_purchase_price"),  # hypothèse : nécessaire pour les réceptions
    ("inventory", "view_stockmovement"), ("inventory", "add_stockmovement"),
    ("inventory", "adjust_stock"),
]
CASHIER_PERMS = [
    ("catalog", "view_category"), ("catalog", "view_product"),
]
ROLE_PERMISSIONS = {
    Role.STOCK_MANAGER: STOCK_MANAGER_PERMS,
    Role.CASHIER: CASHIER_PERMS,
}
