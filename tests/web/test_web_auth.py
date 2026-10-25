import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import Role, User

PWD = "mot-de-passe-de-test-123"  # valeur fictive, tests uniquement


@pytest.fixture
def user(roles):
    return User.objects.create_user(username="vendeur1", password=PWD, role=Role.CASHIER)


def test_login_page_is_public(client):
    resp = client.get(reverse("web:login"))
    assert resp.status_code == 200
    assert b'name="username"' in resp.content and b'name="password"' in resp.content


def test_successful_login_redirects_to_dashboard(client, user):
    resp = client.post(reverse("web:login"), {"username": "vendeur1", "password": PWD})
    assert resp.status_code == 302 and resp.url == reverse("web:dashboard")
    assert "_auth_user_id" in client.session


def test_wrong_password_is_refused(client, user):
    resp = client.post(reverse("web:login"), {"username": "vendeur1", "password": "mauvais"})
    assert resp.status_code == 200
    assert "_auth_user_id" not in client.session


def test_inactive_user_cannot_login(client, user):
    user.is_active = False
    user.save()
    resp = client.post(reverse("web:login"), {"username": "vendeur1", "password": PWD})
    assert resp.status_code == 200 and "_auth_user_id" not in client.session


def test_login_ignores_external_next_url(client, user):
    resp = client.post(reverse("web:login") + "?next=https://evil.example/",
                       {"username": "vendeur1", "password": PWD})
    assert resp.status_code == 302 and resp.url == reverse("web:dashboard")


def test_login_applies_preferred_language_cookie(client, roles):
    User.objects.create_user(username="ar1", password=PWD, role=Role.CASHIER, preferred_language="ar")
    resp = client.post(reverse("web:login"), {"username": "ar1", "password": PWD})
    assert resp.cookies["django_language"].value == "ar"


def test_logout_requires_post(client, user):
    client.force_login(user)
    assert client.get(reverse("web:logout")).status_code == 405
    assert "_auth_user_id" in client.session


def test_logout_post_ends_session(client, user):
    client.force_login(user)
    resp = client.post(reverse("web:logout"))
    assert resp.status_code == 302 and resp.url == reverse("web:login")
    assert "_auth_user_id" not in client.session


def test_logout_needs_csrf_token(user):
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(user)
    assert strict.post(reverse("web:logout")).status_code == 403
    assert "_auth_user_id" in strict.session


def test_authenticated_user_skips_login_page(client, user):
    client.force_login(user)
    resp = client.get(reverse("web:login"))
    assert resp.status_code == 302 and resp.url == reverse("web:dashboard")


def test_root_redirects_to_dashboard(client):
    resp = client.get("/")
    assert resp.status_code == 302 and resp.url == reverse("web:dashboard")
