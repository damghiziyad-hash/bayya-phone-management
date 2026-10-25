import pytest


@pytest.fixture(autouse=True)
def _no_ssl_redirect(settings):
    """En production (DEBUG=False) Django redirige vers HTTPS ; le client de test parle en HTTP."""
    settings.SECURE_SSL_REDIRECT = False
