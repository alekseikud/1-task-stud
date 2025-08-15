from scripts.connection import server_connect,server_disconnect
from dotenv import load_dotenv
from psycopg import Connection,sql
import os,sqlparse,json
from psycopg.sql import Composable
from scripts.logger import logger
from typing import Dict
import logging

load_dotenv()

@logger
def reset_parameters()->None:
    """
    Resets database user and database parameters using admin connection.

    Reads USER, PASSWORD, and DBNAME from environment variables, recreates or
    updates the role with the given password, drops the target database if it
    exists, and creates a new empty database. Revokes privileges before changes.

    Raises
    ------
    ConnectionError
        If admin database connection fails.
    Exception
        If required environment variables are missing or if SQL execution fails.
    """

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
    """
    Grants USAGE and CREATE privileges on the `public` schema to the specified user.

    By default, the target user is read from the USER environment variable.
    Requires an admin connection (non-admin database).

    Raises
    ------
    Exception
        If admin connection fails or no user is specified.
    """

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
    """
    Revokes all privileges on the `public` schema from the specified user.

    By default, the target user is read from the USER environment variable.
    Requires an admin connection (non-admin database).

    Raises
    ------
    Exception
        If admin connection fails or no user is specified.
    """
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
    """
    Creates database tables from the `sql/tables.sql` script.

    Reads and executes each SQL statement in the file sequentially,
    committing after each execution.

    Raises
    ------
    Exception
        If the database connection fails.
    """
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

@logger
def load_funtions()->None:
    """
    Loads database functions from the `sql/functions.sql` script.

    Reads and executes each SQL statement in the file sequentially,
    committing after each execution.

    Raises
    ------
    ConnectionError
        If the database connection fails.
    """
    connection:Connection|None=server_connect()
    if not connection:
       raise ConnectionError
    with open("sql/functions.sql",encoding="UTF-8") as file:
        raw_sql=file.read()
        for q in sqlparse.split(raw_sql):
            with connection.cursor() as cursor:
                query=q.strip()
                if query:
                    cursor.execute(query) #type:ignore
                    connection.commit()

def refresh_view(view_name:str="ages")->None:
    """
    Refreshes the specified materialized view (default: `ages`).

    Ensures the view exists by calling `create_ages_view()`, then runs
    `REFRESH MATERIALIZED VIEW` to update its contents. Used after each
    data insertion to maintain data consistency.

    Raises
    ------
    ConnectionError
        If the database connection fails.
    """
    connection:Connection|None=server_connect()
    if not connection:
        raise ConnectionError
    with connection.cursor() as cursor:
        from scripts.report import create_ages_view
        create_ages_view()#ensure view exist
        cursor.execute("""REFRESH MATERIALIZED VIEW "ages" """)
        connection.commit()

@logger
def insert_data(name:str)->None:
    """
    Inserts data from matching JSON files in `datasets` into the specified table.

    Normalizes values based on table column definitions from `information_schema`,
    skips rows with invalid values, and uses `ON CONFLICT` to avoid duplicate inserts.
    Moves processed files to `datasets/parsed` after insertion.

    Ensures required SQL functions are loaded before inserting. After each successful
    insertion batch, refreshes the `ages` view to keep query results and reports in
    sync with the latest data.

    Raises
    ------
    ValueError
        If no matching JSON files are found or if the table has no columns.
    ConnectionError
        If the database connection fails.
    """
    matching_files=[file for file in os.listdir("datasets") 
                    if name in file and file.endswith(".json") ]
    if not matching_files:
        raise ValueError("No such file in datasets directory")

    connection=server_connect()
    if not connection:
        raise ConnectionError("No such file in datasets directory")
    
    column_parameters=[]
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("""SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns
                            WHERE table_schema=%s and table_name=%s"""),params=("public",name))
        column_parameters=cursor.fetchall()
    if column_parameters is []:
        raise ValueError("No columns in the table")
            # parameter[0] is column name
    norm_dict={parameter[0]:Normalisation(parameter) for parameter in column_parameters}
    for file in matching_files:
        with open("datasets/"+file,encoding="UTF-8") as f:
            data:list[Dict]=json.load(f)
            insertion_list=[]
            for dict in data:
                fail=False
                insertion_tuple=()
                for key in norm_dict.keys():
                    try:
                        value=norm_dict[key].normalise_value(dict[key])
                        insertion_tuple+=(value,)
                    except: #nothing really bad just incorrect value inserted
                        logging.info(f"[WARNING] Value passed in file in {key} column was incorrect.")
                        fail=True
                        break
                if not fail:
                    insertion_list.append(insertion_tuple)
            with connection.cursor() as cursor:
                load_funtions()#check wheather needed functionn is loaded
                query=sql.SQL("""INSERT INTO {} ({}) VALUES({}) 
                              ON CONFLICT ({}) DO UPDATE
                              SET {}=DEFAULT --DUMMY VALUE (Won't be executed)
                              WHERE conflict_resolution(EXCLUDED.{})""").format\
                (
                    sql.Identifier(name),
                    sql.SQL(",").join(map(sql.Identifier,norm_dict.keys())),
                    sql.SQL(",").join(sql.Placeholder()*len(norm_dict.keys())),
                    sql.Identifier(next(iter(norm_dict.keys()))),
                    sql.Identifier(next(iter(norm_dict.keys()))),
                    sql.Identifier(next(iter(norm_dict.keys())))
                )
                cursor.executemany(query,params_seq=insertion_list)
            connection.commit()
        os.system("mkdir datasets/parsed")
        os.system(f"mv datasets/'{file}' datasets/parsed")
    refresh_view()#every insertion we refresh view
                


 
class Normalisation:
    """
    Normalizes values for DB insertion based on column metadata.

    Maps SQL types to Python converters (int, float, str, date) and enforces
    nullability. Raises ValueError for invalid or disallowed null values.

    Raises
    ------
    TypeError
        If the SQL type is unsupported.
    ValueError
        If nullability is violated or conversion fails.
    """
    def __init__(self,parameter:tuple[str,str,str])->None:
        self._col_name,data_type,is_nullable=parameter

        if is_nullable.casefold()=="yes".casefold():
            self._is_nullable=True
        else:
            self._is_nullable=False

        if data_type.casefold() in ("integer", "smallint", "bigint"):
            self._data_type=int
        elif data_type.casefold() in ("numeric", "real", "double precision", "decimal"):
            self._data_type=float
        elif data_type.casefold().startswith("character") or data_type.casefold() == "text":
            self._data_type=str
        elif data_type.casefold() in ("date",):
            from datetime import datetime
            self._data_type= datetime.fromisoformat
        else:
            # Unknown type — raise Error
            raise TypeError("Unknown type")

    def __str__(self)->str: #for debag if needed
        return str(self._col_name)+str(self._data_type)+str(self._is_nullable)
    
    def normalise_value(self,value):
        if value is None and self._is_nullable==False:
            raise ValueError
        from datetime import datetime
        if (self._data_type)==datetime.fromisoformat:
            return datetime.fromisoformat(value)
        try:
            return self._data_type(value)
        except:
            raise ValueError()