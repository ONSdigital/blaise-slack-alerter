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
        timestamp="NOW",
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
        timestamp="NOW",
        platform="cloud_function",
        application="my_app",
    )
