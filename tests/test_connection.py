from scripts.setup_db import server_connect, server_disconnect
from psycopg import Connection
import pytest
import logging


def test_connection_failure_on_invalid_db(monkeypatch) -> None:
    logging.info("[TEST] test_connection_failure_on_invalid_db started")
    # set a temporary env var
    monkeypatch.setenv("DBNAME", "fake_db")
    monkeypatch.setenv("DBUSER", "fake_user")
    monkeypatch.setenv("HOST", "localhost")
    monkeypatch.setenv("PORT", "5432")
    with pytest.raises(ConnectionError):
        connection_failure: Connection | None = server_connect(
            admin=False, admin_db=False
        )
        if connection_failure:  # dummy check for flake8 and ruff
            pass
    server_disconnect(None)
    logging.info("[TEST] test_connection_failure_on_invalid_db finished")


def test_root_connection(monkeypatch) -> None:
    logging.info("[TEST] test_root_connection started")
    monkeypatch.setenv("HOST", "localhost")
    monkeypatch.setenv("PORT", "5432")
    connection: Connection | None = server_connect(admin=True, admin_db=True)
    assert isinstance(connection, Connection)
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        row = cursor.fetchone()
        if row:
            logging.info(row)
            assert "version" in row[0]
        else:
            raise
    server_disconnect(connection)
    logging.info("[TEST] test_root_connection finished")
