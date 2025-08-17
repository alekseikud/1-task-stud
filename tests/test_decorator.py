from scripts.logger import logger
import pytest
from datetime import datetime


@logger
def error_raiser(ex: BaseException) -> None:
    raise ex


class Exception_list:
    def __init__(self):
        self.data: list[dict[Exception, tuple[bool, str]]] = (
            []
        )  # tuple(should exception be rearaised?,codeword in logger)
        self.index = -1

    def _insert(self, ex_dict: dict):
        self.data.append(ex_dict)

    def __iter__(self):
        return self

    def __next__(self):
        self.index += 1
        if self.index == len(self.data):
            raise StopIteration
        return next(iter(self.data[self.index].items()))


def test_logger_exception_catching() -> None:
    exceptions = Exception_list()
    # ----------------------------RANDOM EXCEPTIONS--------------------
    exceptions._insert({Exception: (True, "[ERROR] [UNKNOWN]")})
    exceptions._insert({IndexError: (True, "[ERROR] [UNKNOWN]")})
    exceptions._insert({PermissionError: (True, "[ERROR] [UNKNOWN]")})
    exceptions._insert({AttributeError: (True, "[ERROR] [UNKNOWN]")})

    # ----------------------------KNOWN EXCEPTIONS--------------------
    exceptions._insert({ConnectionError: (True, "[WARNING] [CONNECTION]")})
    exceptions._insert({ValueError: (False, "[WARNING] [VALUE]")})
    exceptions._insert({FileNotFoundError: (False, "[INFO] [FILE]")})

    for exception, (is_rearaised, codeword) in exceptions:
        start_time = datetime.now()
        if is_rearaised:
            with pytest.raises(BaseException):
                error_raiser(exception)
        else:
            error_raiser(exception)
        with open("logger.log", encoding="UTF-8") as file:
            for line in reversed(list(file)):
                if codeword in line:
                    break
                if datetime.strptime(line[0:23], "%Y-%m-%d %H:%M:%S,%f") < start_time:
                    pytest.fail("No mention in loggger.log")
