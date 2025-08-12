import psycopg
from dotenv import load_dotenv
import os,logging
from scripts.logger import logger

load_dotenv()


@logger
def server_connect(admin:bool=False,admin_db:bool=False)->psycopg.Connection|None:
    try:
        db_name=os.getenv("DBNAME")
        user=os.getenv("USER")
        password=os.getenv("PASSWORD")
        if admin:
            user=os.getenv("ADMIN")
            password=os.getenv("ADMIN_PASSWORD")
        if admin_db:
            db_name=os.getenv("ADMIN_DBNAME")
        connection:psycopg.Connection=psycopg.connect(dbname=db_name,user=user,password=password)
        return connection
    except Exception as _ex:
        raise Exception(f"Exception {_ex} ocurred during connection to server")

@logger
def server_disconnect(connection:psycopg.Connection|None)->None:
    if not connection:
        logging.warning("Tried to disconnect None is sever_disconnect function")
    else:
        connection.close()
