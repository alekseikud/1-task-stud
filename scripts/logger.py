import logging
from psycopg.errors import Diagnostic
from psycopg import Connection

logging.basicConfig(
    filename="logger.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def logger(func):
    """
    Decorator that wraps a function with logging of Python and PostgreSQL notice handling.

    - Logs when the function starts and finishes.
    - If the wrapped function returns a psycopg.Connection object,
      attaches a notice handler to log PostgreSQL server messages.
    - Catches ValueError, ConnectionError, and other exceptions,
      logging them with appropriate severity before re-raising.

    *used by all functions for proper logging

    Parameters
    ----------
    func : callable
        The function to wrap.

    Returns
    -------
    callable
        The wrapped function with logging and notice handling.
    """

    def wrapper(*args, **kwargs):

        # shut up the dicttoxml since it produces too many unnecessary info
        logging.getLogger("dicttoxml").setLevel(logging.WARNING)
        logging.info(f"""Function {func.__name__} is opened""")

        def handler(diag: Diagnostic) -> None:
            tag = f"PG-{diag.severity}"
            if diag.severity in ("INFO", "NOTICE"):
                logging.info("[%s] %s", tag, diag.message_primary)
            else:
                logging.warning("[%s] %s", tag, diag.message_primary)

        if "report_to_json" == func.__name__:
            from scripts.setup_db import insert_data

            if not insert_data.need_report_json:
                logging.info(
                    """No need for reporting.
                             Reports are up-to-date"""
                )
                return None
            else:
                insert_data.need_report_json = False
        if "report_to_xml" == func.__name__:
            from scripts.setup_db import insert_data

            if not insert_data.need_report_xml:
                logging.info(
                    """No need for reporting.
                             Reports are up-to-date"""
                )
                return None
            else:
                insert_data.need_report_xml = False
        try:
            result = func(*args, **kwargs)
            logging.info(f"""Function {func.__name__} finished successfully""")
            if isinstance(result, Connection):
                result.add_notice_handler(handler)
            return result
        except FileNotFoundError:
            logging.info("""No files to read from.Skip""")
            return None
        except ValueError as _err:
            logging.warning(
                f"""[VALUE] Function {func.__name__} ran with value error: {_err}"""
            )
        except ConnectionError as _err:
            logging.warning(
                f"""[CONNECTION] Function {func.__name__}
                ran with connection error: {_err}"""
            )
        except BaseException as _ex:
            logging.error(f"""Function {func.__name__} ran with exception: {_ex}""")
            raise

    return wrapper
