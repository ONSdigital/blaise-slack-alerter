import pytest
import datetime
import dataclasses

from lib.log_processor import ProcessedLogEntry
from lib.filters.execute_sql_filter import (
    execute_sql_filter,
)


@pytest.fixture()
def processed_log_entry_execute_sql_error() -> ProcessedLogEntry:
    return ProcessedLogEntry(
        message="cloudsql.instances.executeSql",
        data=dict(methodName="cloudsql.instances.executeSql"),
        severity="ERROR",
        platform="cloudsql_database",
        application="unknown",
        log_name="logs/cloudaudit.googleapis.com/data_access",
        timestamp=datetime.datetime(2024, 8, 1, 5, 52, 34, 24221),
        log_query={
            "resource.type": "cloudsql_database",
            "resource.labels.database_id": "ons-blaise-v2-prod:blaise-prod-123456",
        },
    )


def test_log_is_skipped_when_its_from_cloud_function_when_execute_sql_error(
    processed_log_entry_execute_sql_error: ProcessedLogEntry,
):
    log_is_skipped = execute_sql_filter(processed_log_entry_execute_sql_error)
    assert log_is_skipped is True


def test_log_message_is_not_a_string_when_execute_sql_error(
    processed_log_entry_execute_sql_error: ProcessedLogEntry,
):
    processed_log_entry_execute_sql_error = dataclasses.replace(
        processed_log_entry_execute_sql_error, message=1234
    )
    log_is_skipped = execute_sql_filter(processed_log_entry_execute_sql_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_does_not_contain_execute_sql_error(
    processed_log_entry_execute_sql_error: ProcessedLogEntry,
):
    processed_log_entry_execute_sql_error = dataclasses.replace(
        processed_log_entry_execute_sql_error,
        data=dict(methodName="dummy"),
    )
    log_is_skipped = execute_sql_filter(processed_log_entry_execute_sql_error)

    assert log_is_skipped is False


def test_log_message_is_not_skipped_when_it_contains_severity_info(
    processed_log_entry_execute_sql_error: ProcessedLogEntry,
):
    processed_log_entry_execute_sql_error = dataclasses.replace(
        processed_log_entry_execute_sql_error, severity="INFO"
    )
    log_is_skipped = execute_sql_filter(processed_log_entry_execute_sql_error)

    assert log_is_skipped is False
