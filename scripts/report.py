from scripts.connection import server_connect,server_disconnect
from psycopg import Connection
from psycopg import sql
from psycopg.sql import Composable
from scripts.logger import logger
import os,json,sqlparse


@logger
def create_ages_view()->None:
    with open("sql/create_ages_view.sql",encoding="UTF-8") as file:
        query=file.read().strip()
        connection:Connection|None=server_connect()
        if not connection:
            raise ConnectionError
        with connection.cursor() as cursor:
            cursor.execute(query)
            connection.commit()
        server_disconnect(connection)

@logger
def report_to_json()->None:
    create_ages_view()# ensure view exists
    connection:Connection|None=server_connect()
    if not connection:
        raise ConnectionError
    DIR="sql/reporting"
    REPORT_DIR="reports"
    for file_name in os.listdir(path=DIR):
        with open(f"{DIR}/{file_name}",encoding="UTF-8") as file:
            query=sql.SQL(file.read().strip())
            wrapped_query=sql.SQL("SELECT json_agg(t) FROM ({}) AS t").format(query)
            with connection.cursor() as cursor:
                cursor.execute(wrapped_query)
                result= cursor.fetchone()
            if result:
                with open(f"{REPORT_DIR}/{file_name.removesuffix(".sql")}.json",mode="w") as file:
                    file.write(json.dumps(result[0],indent=4))
            else:
                raise ValueError("No value was returned")
    server_disconnect(connection)
