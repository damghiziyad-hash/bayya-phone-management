from decimal import Decimal

import pytest
from django.urls import reverse

from accounts.models import Role
from catalog.models import Category, Product
from core.models import Status
from inventory.models import MovementType
from inventory.services import record_movement
from web.services import get_dashboard_stats


@pytest.fixture
def catalog_data(db):
    cat = Category.objects.create(name_fr="Batteries")

    def mk(sku, qty, thr, price, status=Status.ACTIVE):
        return Product.objects.create(sku=sku, name_fr=f"Produit {sku}", category=cat, quantity=qty,
                                      low_stock_threshold=thr, purchase_price=Decimal(price), status=status)
    mk("NORMAL", 10, 5, "10.00")
    mk("LOW", 3, 5, "20.50")
    mk("OUT", 0, 5, "99.00")
    mk("ARCH-OUT", 0, 5, "50.00", Status.ARCHIVED)
    mk("ARCH-LOW", 2, 5, "50.00", Status.ARCHIVED)


# ---- accès ----
def test_anonymous_is_redirected_to_login(client):
    resp = client.get(reverse("web:dashboard"))
    assert resp.status_code == 302
    assert resp.url == f"{reverse('web:login')}?next={reverse('web:dashboard')}"



def test_user_without_permission_gets_403(client, make_user):
    u = make_user("noperm", Role.CASHIER)

    client.force_login(u)
    u.groups.clear()
    u.refresh_from_db()

    assert not u.has_perm("catalog.view_product")

    response = client.get(reverse("web:dashboard"))
    assert response.status_code == 403


@pytest.mark.parametrize("role", [Role.OWNER, Role.STOCK_MANAGER, Role.CASHIER])
def test_every_role_can_open_dashboard(client, make_user, role):
    client.force_login(make_user(f"u-{role}", role))
    assert client.get(reverse("web:dashboard")).status_code == 200

# ---- indicateurs réels ----
def test_stats_are_computed_from_database_and_exclude_archived(owner, catalog_data):
    s = get_dashboard_stats(owner)
    assert s["active_count"] == 3
    assert s["total_quantity"] == 13
    assert s["low_count"] == 1
    assert s["out_count"] == 1
    assert s["stock_value"] == Decimal("161.50")  # 10×10.00 + 3×20.50 + 0×99.00
    assert [p.sku for p in s["watch_list"]] == ["OUT", "LOW"]  # rupture d'abord, archivés exclus


def test_stats_on_empty_database(owner, db):
    s = get_dashboard_stats(owner)
    assert (s["active_count"], s["total_quantity"], s["low_count"], s["out_count"]) == (0, 0, 0, 0)
    assert s["stock_value"] == Decimal("0") and s["watch_list"] == [] and s["recent_movements"] == []


def test_dashboard_page_shows_numbers(client, owner, catalog_data):
    client.force_login(owner)
    html = client.get(reverse("web:dashboard")).content.decode()
    assert 'id="stat-active">3<' in html and 'id="stat-quantity">13<' in html
    assert 'id="stat-low">1<' in html and 'id="stat-out">1<' in html
    assert "Produit OUT" in html and "Produit ARCH-OUT" not in html


def test_dashboard_empty_states(client, owner, db):
    client.force_login(owner)
    html = client.get(reverse("web:dashboard")).content.decode()
    assert "Aucun produit à surveiller" in html and "Aucun mouvement de stock enregistré" in html


# ---- visibilité selon les permissions ----
def test_cashier_sees_neither_value_nor_movements(client, cashier, catalog_data):
    s = get_dashboard_stats(cashier)
    assert s["stock_value"] is None and s["recent_movements"] is None
    client.force_login(cashier)
    html = client.get(reverse("web:dashboard")).content.decode()
    assert 'id="stat-value"' not in html and "Derniers mouvements de stock" not in html


def test_stock_manager_sees_value_and_movements(client, stock_manager, catalog_data):
    client.force_login(stock_manager)
    html = client.get(reverse("web:dashboard")).content.decode()
    assert 'id="stat-value"' in html and "Derniers mouvements de stock" in html


def test_recent_movements_are_limited_and_newest_first(owner, stock_manager, category):
    p = Product.objects.create(sku="MV", name_fr="Mouvements", category=category)
    for _ in range(12):
        record_movement(product=p, movement_type=MovementType.IN, quantity=1, user=stock_manager)
    moves = get_dashboard_stats(owner)["recent_movements"]
    assert len(moves) == 10
    assert moves[0].quantity_after == 12  # le plus récent en premier
