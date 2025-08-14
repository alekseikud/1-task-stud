from scripts.connection import server_connect,server_disconnect
from psycopg import Connection
from psycopg import sql
from psycopg.sql import Composable
from scripts.logger import logger
import os

@logger
def rooms_stud_number()->None:
    query="""
        SELECT r.*,COUNT(*)
        FROM rooms r
        JOIN students s ON r.id=s.room
        GROUP BY r.id,r.name
        ORDER BY count DESC
        """
    json:str=execute_query(query)
    os.system("mkdir reports")
    with open(file="reports/rooms_stud_number.json",mode="w") as file:
        file.write(json)

@logger
def create_ages_view()->None:
    query="""
        CREATE MATERIALIZED VIEW IF NOT EXISTS ages AS
        (
            SELECT s.*,
            (CURRENT_DATE-s.birthday)/365 AS age
            FROM students s
        )
        """
    connection:Connection|None=server_connect()
    if not connection:
        raise ConnectionError
    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()
    server_disconnect(connection)


@logger
def rooms_lowest_avg_age(row_num:int=5)->None:
    query=sql.SQL(
        """
        SELECT r.id,r.name,AVG(a.age) AS average_age
        FROM ages a
        JOIN rooms r
        ON a.room=r.id
        GROUP BY r.id,r.name
        ORDER BY average_age
        LIMIT {}
        """).format(sql.Literal(row_num))
    json:str=execute_query(query)
    os.system("mkdir reports")
    with open(file="reports/rooms_lowest_avg_age.json",mode="w") as file:
        file.write(json)

@logger
def rooms_highest_age_diff(row_num:int=5)->None:
    query=sql.SQL(
        """
        SELECT r.*,(MAX(a.age)-MIN(a.age)) AS age_difference
        FROM rooms r
        JOIN ages a ON r.id=a.room
        GROUP BY r.id,r.name
        ORDER BY age_difference DESC
        LIMIT {}
        """).format(sql.Literal(row_num))
    json:str=execute_query(query)
    os.system("mkdir reports")
    with open(file="reports/rooms_highest_age_diff.json",mode="w") as file:
        file.write(json)

@logger
def rooms_different_sex()->None:
    query=  """
            SELECT * FROM
            (
                SELECT r.name,s.room,
                COUNT(
                    CASE WHEN sex='M' THEN 1
                    END
                ) AS male_count,
                COUNT(
                    CASE WHEN sex='F' THEN 1
                    END
                ) AS female_count
                FROM rooms r
                JOIN students s
                ON r.id=s.room
                GROUP BY r.name,s.room
            )
            WHERE male_count>0 AND female_count>0
            """
    json:str=execute_query(query)
    os.system("mkdir reports")
    with open(file="reports/rooms_different_sex.json",mode="w") as file:
        file.write(json)
@logger
def execute_query(query:str|Composable)->str:
    create_ages_view()# ensure view exists
    connection:Connection|None=server_connect()
    if not connection:
        raise ConnectionError
    if not isinstance(query,Composable):
        query=sql.SQL(query)
    wrapped_query=sql.SQL("SELECT json_agg(t) FROM ({}) AS t").format(query)
    with connection.cursor() as cursor:
        cursor.execute(wrapped_query)
        result= cursor.fetchone()
    server_disconnect(connection)
    if result:
        return str(result[0])
    else:
        raise ValueError("No value was returned")

