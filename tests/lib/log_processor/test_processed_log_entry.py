from datetime import datetime

from dateutil.parser import parse
import pytz

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor import AppLogPayload
from lib.log_processor import ProcessedLogEntry
from lib.log_processor.processed_log_entry import create_processed_log_entry


def test_create_processed_log_entry():
    log_entry = LogEntry(
        resource_type="ignored",
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload="ignore",
        severity="WARN",
        log_name="/example_log",
        timestamp="2022-07-22T20:36:21.891133Z",
        labels=dict(),
    )
    app_log_payload = AppLogPayload(
        message="there was an error",
        data=dict(key="example_value"),
        platform="cloud_function",
        application="my_app",
        most_important_values=["important_value"],
    )
    result = create_processed_log_entry(log_entry, app_log_payload)

    assert result == ProcessedLogEntry(
        message="there was an error",
        data=dict(key="example_value"),
        severity="WARN",
        log_name="/example_log",
        timestamp=parse("2022-07-22T20:36:21.891133Z").astimezone(
            pytz.timezone("Europe/London")
        ),
        platform="cloud_function",
        application="my_app",
        most_important_values=["important_value"],
    )


def test_create_processed_log_entry_when_timestamp_is_missing():
    log_entry = LogEntry(
        resource_type="ignored",
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload="ignore",
        severity="WARN",
        log_name="/example_log",
        timestamp=None,
        labels=dict(),
    )
    app_log_payload = AppLogPayload(
        message="there was an error",
        data=dict(key="example_value"),
        platform="cloud_function",
        application="my_app",
    )
    result = create_processed_log_entry(log_entry, app_log_payload)

    assert result == ProcessedLogEntry(
        message="there was an error",
        data=dict(key="example_value"),
        severity="WARN",
        log_name="/example_log",
        timestamp=None,
        platform="cloud_function",
        application="my_app",
    )


def test_create_processed_log_entry_when_timestamp_not_parseable():
    log_entry = LogEntry(
        resource_type="ignored",
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload="ignore",
        severity="WARN",
        log_name="/example_log",
        timestamp="this is not a datetime",
        labels=dict(),
    )
    app_log_payload = AppLogPayload(
        message="there was an error",
        data=dict(key="example_value"),
        platform="cloud_function",
        application="my_app",
        log_query=dict(field1="value1", field2="value2"),
    )
    result = create_processed_log_entry(log_entry, app_log_payload)

    assert result == ProcessedLogEntry(
        message="there was an error",
        data=dict(key="example_value"),
        severity="WARN",
        log_name="/example_log",
        timestamp=None,
        platform="cloud_function",
        application="my_app",
        log_query=dict(field1="value1", field2="value2"),
    )
