from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import override

from catalog.models import Category, Product, StockStatus
from core.models import Status


def make(category, sku, **kw):
    return Product.objects.create(sku=sku, name_fr="Pièce", category=category, **kw)


def test_create_category_and_product(category):
    p = make(category, "bat-001", sale_price=Decimal("120.50"))
    assert p.pk and p.category == category and p.status == Status.ACTIVE
    assert p.created_at and p.updated_at


def test_sku_is_normalized_and_unique(category):
    p = make(category, "  abc-1 ")
    assert p.sku == "ABC-1"
    with pytest.raises(IntegrityError), transaction.atomic():
        make(category, "abc-1")


def test_barcode_unique_only_when_filled(category):
    make(category, "A1", barcode="")
    make(category, "A2", barcode="")  # plusieurs vides autorisés
    make(category, "A3", barcode="6111111111111")
    with pytest.raises(IntegrityError), transaction.atomic():
        make(category, "A4", barcode="6111111111111")


def test_negative_prices_are_rejected(category):
    p = Product(sku="NEG", name_fr="x", category=category, purchase_price=Decimal("-1"))
    with pytest.raises(ValidationError) as exc:
        p.full_clean()
    assert "purchase_price" in exc.value.message_dict


def test_negative_price_rejected_by_database(category):
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.bulk_create([Product(sku="NEG2", name_fr="x", category=category, sale_price=Decimal("-5"))])


def test_money_uses_exact_decimals(category):
    p = make(category, "DEC", sale_price=Decimal("0.10"))
    p.refresh_from_db()
    assert p.sale_price + Decimal("0.20") == Decimal("0.30")


def test_stock_status(category):
    p = make(category, "ST", quantity=0, low_stock_threshold=5)
    assert p.stock_status == StockStatus.OUT
    p.quantity = 5
    assert p.stock_status == StockStatus.LOW
    p.quantity = 6
    assert p.stock_status == StockStatus.NORMAL
    p.status = Status.ARCHIVED
    assert p.stock_status == StockStatus.ARCHIVED


def test_display_name_falls_back_when_translation_missing(category):
    p = make(category, "I18N", name_ar="")
    with override("ar"):
        assert p.display_name == "Pièce"  # pas de nom arabe : repli sur le français
        assert category.display_name == "شاشات"
    with override("fr"):
        assert category.display_name == "Écrans"
