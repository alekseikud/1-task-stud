from scripts.setup_db import Normalisation
from scripts.logger import logger
import pytest
import logging


class test_class:
    def __init__(self) -> None:
        pass

    def __str__(self):
        raise TypeError("Cannot be converted to string")


@logger
def test_normalisation() -> None:
    pg_types = [
        "integer",
        "smallint",
        "bigint",
        "date",
        "numeric",
        "real",
        "double precision",
        "decimal",
        "character something",
        "text",
    ]
    pg_values = [
        1,
        2,
        3,
        "2011-08-22T00:00:00.000000",
        1.1,
        1.2,
        1.3,
        1.4,
        "a",
        "sometext",
    ]
    not_string = test_class()
    incorrect_pg_values = [
        1.1,
        1.2,
        1.3,
        "a",
        "t",
        "t",
        "t",
        "t",
        not_string,
        not_string,
    ]
    test_parameters = [
        Normalisation(("somecolumn", some_type, "NO")) for some_type in pg_types
    ]
    error_count = 0
    for test, value in zip(test_parameters, pg_values):
        try:
            test.normalise_value(str(value))
        except (ValueError, TypeError) as _err:
            logging.warning(f"[TEST] Cannot cast.Error{_err}")
            error_count += 1
    assert error_count == 0

    for test, value in zip(test_parameters, incorrect_pg_values):
        with pytest.raises((ValueError, TypeError)):
            test.normalise_value(str(value))
