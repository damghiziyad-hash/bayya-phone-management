from django.db import connection


def test_database_connection_works(db):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1


def test_project_uses_expected_engine(settings):
    assert connection.vendor in {"postgresql", "sqlite"}
