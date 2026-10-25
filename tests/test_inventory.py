import threading

import pytest
from django.core.exceptions import PermissionDenied
from django.db import connection

from core.exceptions import ImmutableRecordError
from core.models import AuditLog, Status
from inventory.models import MovementType, StockMovement
from inventory.services import InsufficientStock, StockError, record_movement, reverse_movement


def test_entry_increases_stock_and_records_before_after(product, stock_manager):
    m = record_movement(product=product, movement_type=MovementType.IN, quantity=5, user=stock_manager)
    product.refresh_from_db()
    assert product.quantity == 15
    assert (m.quantity_before, m.quantity_after) == (10, 15)
    assert m.created_by == stock_manager


def test_exit_decreases_stock(product, stock_manager):
    record_movement(product=product, movement_type=MovementType.OUT, quantity=4, user=stock_manager)
    product.refresh_from_db()
    assert product.quantity == 6


def test_negative_stock_is_refused_and_nothing_is_written(product, stock_manager):
    count = StockMovement.objects.count()
    with pytest.raises(InsufficientStock):
        record_movement(product=product, movement_type=MovementType.OUT, quantity=11, user=stock_manager)
    product.refresh_from_db()
    assert product.quantity == 10 and StockMovement.objects.count() == count


@pytest.mark.parametrize("qty", [0, -3, 1.5, "2", True, None])
def test_invalid_quantities_are_refused(product, stock_manager, qty):
    with pytest.raises(StockError):
        record_movement(product=product, movement_type=MovementType.IN, quantity=qty, user=stock_manager)


def test_adjustment_requires_reason_and_is_audited(product, stock_manager):
    with pytest.raises(StockError):
        record_movement(product=product, movement_type=MovementType.ADJUST_MINUS, quantity=1, user=stock_manager, reason="  ")
    record_movement(product=product, movement_type=MovementType.ADJUST_MINUS, quantity=1,
                    user=stock_manager, reason="pièce cassée")
    product.refresh_from_db()
    assert product.quantity == 9
    assert AuditLog.objects.filter(action="stock.adjustment", user=stock_manager).exists()


def test_cashier_cannot_move_or_adjust_stock(product, cashier):
    for t in (MovementType.IN, MovementType.OUT):
        with pytest.raises(PermissionDenied):
            record_movement(product=product, movement_type=t, quantity=1, user=cashier)
    with pytest.raises(PermissionDenied):
        record_movement(product=product, movement_type=MovementType.ADJUST_PLUS, quantity=1, user=cashier, reason="x")
    product.refresh_from_db()
    assert product.quantity == 10


def test_anonymous_user_is_refused(product):
    with pytest.raises(PermissionDenied):
        record_movement(product=product, movement_type=MovementType.IN, quantity=1, user=None)


def test_archived_product_refuses_movements(product, stock_manager):
    product.status = Status.ARCHIVED
    product.save()
    with pytest.raises(StockError):
        record_movement(product=product, movement_type=MovementType.IN, quantity=1, user=stock_manager)


def test_movements_are_immutable(product, stock_manager):
    m = StockMovement.objects.filter(product=product).first()
    m.reason = "modifié"
    with pytest.raises(ImmutableRecordError):
        m.save()
    with pytest.raises(ImmutableRecordError):
        m.delete()
    with pytest.raises(ImmutableRecordError):
        StockMovement.objects.filter(pk=m.pk).update(quantity=99)
    with pytest.raises(ImmutableRecordError):
        StockMovement.objects.all().delete()


def test_reversal_creates_compensating_movement_and_keeps_history(product, stock_manager):
    original = record_movement(product=product, movement_type=MovementType.OUT, quantity=3, user=stock_manager)
    rev = reverse_movement(movement=original, user=stock_manager, reason="erreur de saisie")
    product.refresh_from_db()
    assert product.quantity == 10
    assert rev.reverses == original and rev.movement_type == MovementType.IN
    assert StockMovement.objects.filter(pk=original.pk).exists()
    assert AuditLog.objects.filter(action="stock.reversal").exists()


def test_cannot_reverse_twice_or_reverse_a_reversal(product, stock_manager):
    original = record_movement(product=product, movement_type=MovementType.OUT, quantity=3, user=stock_manager)
    rev = reverse_movement(movement=original, user=stock_manager, reason="erreur")
    original.refresh_from_db()
    with pytest.raises(StockError):
        reverse_movement(movement=original, user=stock_manager, reason="encore")
    with pytest.raises(StockError):
        reverse_movement(movement=rev, user=stock_manager, reason="annuler l'annulation")


def test_cashier_cannot_reverse(product, stock_manager, cashier):
    original = record_movement(product=product, movement_type=MovementType.OUT, quantity=1, user=stock_manager)
    with pytest.raises(PermissionDenied):
        reverse_movement(movement=original, user=cashier, reason="x")


def test_quantity_always_matches_movement_history(product, stock_manager):
    record_movement(product=product, movement_type=MovementType.OUT, quantity=2, user=stock_manager)
    record_movement(product=product, movement_type=MovementType.IN, quantity=7, user=stock_manager)
    record_movement(product=product, movement_type=MovementType.ADJUST_MINUS, quantity=1, user=stock_manager, reason="inventaire")
    sign = {"in": 1, "adjust_plus": 1, "out": -1, "adjust_minus": -1}
    total = sum(sign[m.movement_type] * m.quantity for m in StockMovement.objects.filter(product=product))
    product.refresh_from_db()
    assert product.quantity == total == 14


@pytest.mark.skipif(connection.vendor != "postgresql", reason="verrous de lignes : PostgreSQL requis")
@pytest.mark.django_db(transaction=True)
def test_concurrent_exits_cannot_oversell_last_piece(category, stock_manager):
    from catalog.models import Product
    p = Product.objects.create(sku="LAST", name_fr="Dernière pièce", category=category)
    record_movement(product=p, movement_type=MovementType.IN, quantity=1, user=stock_manager)
    results = []

    def worker():
        try:
            record_movement(product=Product.objects.get(pk=p.pk), movement_type=MovementType.OUT, quantity=1, user=stock_manager)
            results.append("ok")
        except InsufficientStock:
            results.append("refused")
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    p.refresh_from_db()
    assert sorted(results) == ["ok", "refused", "refused", "refused"]
    assert p.quantity == 0
