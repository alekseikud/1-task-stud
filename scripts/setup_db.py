from scripts.connection import server_connect,server_disconnect
from dotenv import load_dotenv
from psycopg import Connection,sql
import os,sqlparse
from scripts.logger import logger

load_dotenv()

@logger
def reset_parameters()->None:
    connection:Connection|None=server_connect(admin=True,admin_db=True)#admin connection
    if not connection:
        raise ConnectionError(f"Cannot connect with admin parameters")
    role=os.getenv("USER")
    password=os.getenv("PASSWORD")
    db_name=os.getenv("DBNAME")
    connection.autocommit=True
    if not role:
        raise Exception(f"No such parameter as USER in .env file")
    if not db_name:
        raise Exception(f"No such parameter as DBNAME in .env file")
    if not password:
        raise Exception(f"No such parameter as PASSWORD in .env file")

    sql_create_role= \
    sql.SQL(""" DO $$
        BEGIN
            BEGIN
                CREATE ROLE {f_role} WITH LOGIN PASSWORD {f_password};
            EXCEPTION
                WHEN duplicate_object THEN
                    ALTER ROLE {f_role} WITH LOGIN PASSWORD {f_password};
                    RAISE NOTICE '{f_role} already exists. Changed password';
                WHEN others THEN
                    RAISE ;
            END;
        END
        $$;
    """).format(
            f_password=sql.Literal(password),
            f_role=sql.Identifier(role)
        )
    
    drop_db=sql.SQL("DROP DATABASE IF EXISTS ")+ \
            sql.Identifier(db_name)+\
            sql.SQL(" WITH (FORCE)")

    create_db=sql.SQL("CREATE DATABASE ")+ \
              sql.Identifier(db_name)
    
    revoke_priveleges()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query=sql_create_role)
            cursor.execute(query=drop_db)
            cursor.execute(query=create_db)

    except Exception as _ex:
        raise Exception(f"Exception ocurred during resetting parametrs. Exception: {_ex}")
    finally:
        server_disconnect(connection)

@logger
def grant_priveleges(user:str|None=os.getenv("USER"))->None:
    connection:Connection|None=server_connect(admin=True,admin_db=False)
    if not connection:
        raise Exception("Cannot connect to postgres superuser")
    if not user:
        raise Exception("No user specified in .env file")
    query=sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO ")+sql.Identifier(user)
    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()
    server_disconnect(connection)

@logger
def revoke_priveleges(user:str|None=os.getenv("USER"))->None:
    connection:Connection|None=server_connect(admin=True,admin_db=False)
    if not connection:
        raise Exception("Cannot connect to postgres superuser")
    if not user:
        raise Exception("No user specified in .env file")
    query=sql.SQL("REVOKE ALL PRIVILEGES ON SCHEMA public FROM ")+sql.Identifier(user)
    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()
    server_disconnect(connection)

@logger
def create_tables()->None:
    connection:Connection|None=server_connect()
    if not connection:
        raise Exception("Cannot connect to DB")
    with open("sql/tables.sql",encoding="UTF-8") as file:
        raw_sql=file.read()
        with connection.cursor() as cursor:
            for q in sqlparse.split(raw_sql):
                query=q.strip()
                if query:
                    cursor.execute(query) #type:ignore
                    connection.commit()