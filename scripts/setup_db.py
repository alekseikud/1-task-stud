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

@logger
def insert_data(name:str)->None:
    matching_files=[file for file in os.listdir("datasets") if name in file and file.endswith(".json") ]
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
    
    norm_dict={parameter[0]:Normalisation(parameter) for parameter in column_parameters}# parameter[0] is column name
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
                query=sql.SQL("""INSERT INTO {} ({}) VALUES({})""").format\
                (
                    sql.Identifier(name),
                    sql.SQL(",").join(map(sql.Identifier,norm_dict.keys())),
                    sql.SQL(",").join(sql.Placeholder()*len(norm_dict.keys()))
                )
                for itr in insertion_list:
                    print(itr)
                cursor.executemany(query,params_seq=insertion_list)
            connection.commit()
        os.system("mkdir datasets/parsed")
        os.system(f"mv datasets/'{file}' datasets/parsed")
        print(f"mv datasets/'{file}' datasets/parsed")
                


 
class Normalisation:
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

    def __str__(self)->str:
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