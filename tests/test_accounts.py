import pytest

from accounts.models import Role, User


def test_user_gets_group_matching_role(cashier):
    assert list(cashier.groups.values_list("name", flat=True)) == [Role.CASHIER]


def test_role_change_updates_group_and_permissions(cashier):
    cashier.role = Role.STOCK_MANAGER
    cashier.save()
    fresh = User.objects.get(pk=cashier.pk)
    assert list(fresh.groups.values_list("name", flat=True)) == [Role.STOCK_MANAGER]
    assert fresh.has_perm("inventory.adjust_stock")


def test_superuser_defaults_to_owner_role(roles):
    su = User.objects.create_superuser("root", "root@example.com", "mot-de-passe-de-test-123")
    assert su.role == Role.OWNER and su.is_staff


def test_owner_has_all_permissions(owner):
    for perm in ("accounts.add_user", "inventory.adjust_stock", "catalog.view_purchase_price", "core.view_auditlog"):
        assert owner.has_perm(perm), perm


def test_stock_manager_permissions(stock_manager):
    assert stock_manager.has_perm("catalog.change_product")
    assert stock_manager.has_perm("inventory.add_stockmovement")
    assert stock_manager.has_perm("inventory.adjust_stock")
    assert not stock_manager.has_perm("accounts.add_user")
    assert not stock_manager.has_perm("core.view_auditlog")


def test_cashier_is_read_only_on_catalog(cashier):
    assert cashier.has_perm("catalog.view_product")
    for perm in ("catalog.add_product", "catalog.change_product", "catalog.view_purchase_price",
                 "inventory.add_stockmovement", "inventory.adjust_stock", "accounts.add_user"):
        assert not cashier.has_perm(perm), perm


def test_inactive_user_has_no_permissions(owner):
    owner.is_active = False
    owner.save()
    assert not User.objects.get(pk=owner.pk).has_perm("inventory.adjust_stock")
