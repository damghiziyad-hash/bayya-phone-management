import pytest
from django.core.management import call_command

from accounts.models import Role, User
from catalog.models import Category, Product
from inventory.models import MovementType
from inventory.services import record_movement

PWD = "mot-de-passe-de-test-123"  # valeur fictive, tests uniquement


@pytest.fixture
def roles(db):
    call_command("setup_roles")


@pytest.fixture
def make_user(roles):
    def _make(username, role):
        return User.objects.create_user(username=username, password=PWD, role=role)
    return _make


@pytest.fixture
def owner(make_user):
    return make_user("owner1", Role.OWNER)


@pytest.fixture
def stock_manager(make_user):
    return make_user("stock1", Role.STOCK_MANAGER)


@pytest.fixture
def cashier(make_user):
    return make_user("cashier1", Role.CASHIER)


@pytest.fixture
def category(db):
    return Category.objects.create(name_fr="Écrans", name_ar="شاشات")


@pytest.fixture
def product(category, stock_manager):
    p = Product.objects.create(sku="ecr-001", name_fr="Écran iPhone 12", category=category,
                               phone_brand="Apple", phone_model="iPhone 12")
    record_movement(product=p, movement_type=MovementType.IN, quantity=10, user=stock_manager,
                    reference="stock initial (fictif)")
    p.refresh_from_db()
    return p
