from logging import LogRecord

import pytest


@pytest.fixture()
def log_matching(caplog):
    def search(levelno: int, message: str) -> LogRecord:
        found = None
        for record in caplog.records:
            if record.levelno == levelno and record.message == message:
                found = record
                break

        assert found, f"Log not found :: {levelno} {message}"
        return found

    return search
