import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from accounts.models import Role, User


def switch(client, language, **extra):
    return client.post(reverse("web:set_language"), {"language": language, "next": reverse("web:login"), **extra})


def test_default_language_is_french_ltr(client):
    html = client.get(reverse("web:login")).content.decode()
    assert 'lang="fr"' in html and 'dir="ltr"' in html
    assert "bootstrap.min." in html and "bootstrap.rtl.min." not in html


def test_anonymous_can_switch_to_arabic_rtl(client):
    resp = switch(client, "ar")
    assert resp.status_code == 302 and resp.url == reverse("web:login")
    assert resp.cookies[settings.LANGUAGE_COOKIE_NAME].value == "ar"
    html = client.get(reverse("web:login")).content.decode()
    assert 'lang="ar"' in html and 'dir="rtl"' in html
    assert "bootstrap.rtl.min." in html


def test_dashboard_is_rtl_in_arabic(client, owner):
    client.force_login(owner)
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "ar"
    html = client.get(reverse("web:dashboard")).content.decode()
    assert 'dir="rtl"' in html


def test_switch_saves_preference_for_logged_in_user(client, cashier):
    client.force_login(cashier)
    switch(client, "ar")
    assert User.objects.get(pk=cashier.pk).preferred_language == "ar"
    switch(client, "fr")
    assert User.objects.get(pk=cashier.pk).preferred_language == "fr"


def test_switch_does_not_reset_user_group(client, cashier):
    client.force_login(cashier)
    switch(client, "ar")
    assert list(User.objects.get(pk=cashier.pk).groups.values_list("name", flat=True)) == [Role.CASHIER]


def test_unknown_language_is_ignored(client, cashier):
    client.force_login(cashier)
    switch(client, "xx")
    assert User.objects.get(pk=cashier.pk).preferred_language == "fr"


def test_switch_requires_post(client):
    assert client.get(reverse("web:set_language")).status_code == 405


def test_switch_needs_csrf_token():
    assert Client(enforce_csrf_checks=True).post(reverse("web:set_language"), {"language": "ar"}).status_code == 403


def test_switch_refuses_external_redirect(client):
    resp = client.post(reverse("web:set_language"), {"language": "ar", "next": "https://evil.example/"})
    assert resp.status_code == 302 and resp.url == "/"
