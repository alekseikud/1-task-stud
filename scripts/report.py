from scripts.connection import server_connect, server_disconnect
from psycopg import Connection
from psycopg import sql
from scripts.logger import logger
import os
import json
from datetime import datetime


@logger
def create_ages_view() -> None:
    """
    Creates the `ages` view in the connected PostgreSQL database.

    Reads and executes the SQL script from `sql/create_ages_view.sql`.
    Commits the transaction and closes the connection when done.

    This function is also used as a prerequisite check in other parts
    of the application: it ensures the `ages_view` exists and creates it
    if it is missing.

    Raises
    ------
    ConnectionError
        If a database connection cannot be established.
    """
    with open("sql/create_ages_view.sql", encoding="UTF-8") as file:
        query = file.read().strip()
        connection: Connection | None = server_connect()
        if not connection:
            raise ConnectionError
        with connection.cursor() as cursor:
            cursor.execute(query)  # type:ignore
            connection.commit()
        server_disconnect(connection)


@logger
def report_to_json() -> None:
    """
    Generates JSON reports from SQL files in `sql/reporting`.

    Runs each `.sql` as a `json_agg` query,
    and saves results as timestamped `.json` files in `reports/json`.

    Raises
    ------
    ConnectionError
        If the database connection fails.
    ValueError
        If a query returns no results.
    """
    create_ages_view()  # ensure view exists
    connection: Connection | None = server_connect()
    if not connection:
        raise ConnectionError
    DIR = "sql/reporting"
    REPORT_DIR = "reports/json"
    # ensures that reporting directory exists
    os.makedirs(REPORT_DIR, exist_ok=True)
    for file_name in os.listdir(path=DIR):
        file_name_no_suff = file_name.removesuffix(".sql")
        with open(f"{DIR}/{file_name}", encoding="UTF-8") as file:
            query = sql.SQL(file.read().strip())  # type:ignore
            wrapped_query = sql.SQL(
                "SELECT json_agg(t) \
                                    FROM ({}) AS t"
            ).format(query)
            with connection.cursor() as cursor:
                cursor.execute(wrapped_query)
                result = cursor.fetchone()
            if result:
                with open(
                    f"{REPORT_DIR}/{file_name_no_suff}{datetime.now()}.json", mode="w"
                ) as w_file:
                    w_file.write(json.dumps(result[0], indent=4))
            else:
                raise ValueError("No value was returned")
    server_disconnect(connection)


def report_to_xml() -> None:
    """
    Generates XML reports from SQL files in `sql/reporting`.

    Runs each `.sql` as a `json_agg` query,
    converts results to XML, and saves them as timestamped `.xml` files
    in `reports/xml`.

    Raises
    ------
    ConnectionError
        If the database connection fails.
    ValueError
        If a query returns no results.
    TypeError
        If the XML serialization does not return a string.
    """
    create_ages_view()  # ensure view exists
    connection: Connection | None = server_connect()
    if not connection:
        raise ConnectionError
    DIR = "sql/reporting"
    REPORT_DIR = "reports/xml"
    # ensures that reporting directory exists
    os.makedirs(REPORT_DIR, exist_ok=True)
    for file_name in os.listdir(DIR):
        file_name_no_suff = file_name.removesuffix(".sql")
        with open(f"{DIR}/{file_name}", encoding="UTF-8") as file:
            query = sql.SQL(file.read().strip())  # type:ignore
            with connection.cursor() as cursor:
                wrapped_query = sql.SQL("SELECT json_agg(t) FROM ({}) AS t").format(
                    query
                )
                cursor.execute(wrapped_query)
                result = cursor.fetchone()
                if result:
                    from dicttoxml import dicttoxml

                    with open(
                        f"{REPORT_DIR}/{file_name_no_suff}{datetime.now()}.xml",
                        mode="w",
                    ) as w_file:
                        from xml.dom.minidom import parseString

                        raw_xml = dicttoxml(
                            result[0],
                            custom_root=file_name_no_suff,
                            item_func=lambda _: "row",
                            attr_type=False,
                            return_bytes=False,
                        )
                        to_write = parseString(raw_xml).toprettyxml(indent="   ")
                        # ensure that reporting directory exists
                        if isinstance(to_write, str):
                            w_file.write(to_write)
                        else:
                            raise TypeError
