import psycopg
from dotenv import load_dotenv
import os
import logging
from scripts.logger import logger

load_dotenv()


@logger
def server_connect(
    admin: bool = False, admin_db: bool = False
) -> psycopg.Connection | None:
    try:
        db_name = os.getenv("DBNAME")
        user = os.getenv("DBUSER")
        password = os.getenv("PASSWORD")
        host = os.getenv("HOST")
        if admin:
            user = os.getenv("ADMIN")
            password = os.getenv("ADMIN_PASSWORD")
        if admin_db:
            db_name = os.getenv("ADMIN_DBNAME")
        connection: psycopg.Connection = psycopg.connect(
            dbname=db_name, user=user, password=password, host=host
        )
        return connection
    except ConnectionError as _ex:
        raise ConnectionError(f"Exception {_ex} ocurred during connection to server")


@logger
def server_disconnect(connection: psycopg.Connection | None) -> None:
    if not connection:
        logging.warning(
            "None passed as connection as a \
                        sever_disconnect function argument"
        )
    else:
        connection.close()
