import logging
from psycopg.errors import Diagnostic
from psycopg import Connection

logging.basicConfig(
    filename="logger.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def logger(func):
    def wrapper(*args, **kwargs):
        logging.info(f"""Function {func.__name__} is opened""")

        def handler(diag:Diagnostic)->None:
            tag = f"PG-{diag.severity}"
            if diag.severity in ("INFO", "NOTICE"):
                logging.info("[%s] %s", tag, diag.message_primary)
            else:
                logging.warning("[%s] %s", tag, diag.message_primary)

        try:
            result=func(*args,**kwargs)
            logging.info(f"""Function {func.__name__} finished successfully""")
            if isinstance(result,Connection):
                result.add_notice_handler(handler)
            return result
        except Exception as _ex:
            logging.error(f"""Function {func.__name__} ran with exception: {_ex}""")
            raise

    return wrapper
