import logging

from flask import Request

from main import log_error


def test_log_error(caplog):
    request = Request.from_values()
    with caplog.at_level(logging.ERROR):
        response = log_error(request)
    log_entries = [record for record in caplog.records]
    assert log_entries[0].levelno == logging.ERROR
    assert log_entries[0].message == "Example error message"
    assert log_entries[0].reason == "proof_of_concept"
    assert response == "Error logged"
