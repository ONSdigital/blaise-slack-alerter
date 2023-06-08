from dateutil.parser import parse

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor import ProcessedLogEntry
from lib.log_processor.app_log_payload_factories import APP_LOG_PAYLOAD_FACTORIES
from lib.log_processor import process_log_entry


def test_parse_log_entry_with_compute_engine_instance_log():
    log_entry = LogEntry(
        resource_type="gce_instance",
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload=dict(
            computer_name="my-vm", extra_info="extra data", message="GAE error message"
        ),
        severity=None,
        log_name=None,
        timestamp=None,
        labels=dict(my_label="my_value"),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(
        message="GAE error message",
        platform="gce_instance",
        application="my-vm",
        data=dict(extra_info="extra data"),
        log_query={"resource.type": "gce_instance"},
        most_important_values=["description", "event_type"],
    )


def test_parse_log_entry_with_json_payload():
    log_entry = LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.JSON,
        payload=dict(
            info="message info",
            extra_info="extra data",
        ),
        severity=None,
        log_name=None,
        timestamp=None,
        labels=dict(),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(
        message="Unknown JSON Error",
        platform=None,
        application=None,
        data=dict(
            info="message info",
            extra_info="extra data",
        ),
    )


def test_parse_log_entry_with_text_payload():
    log_entry = LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp=None,
        labels=dict(),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(message="example error")


def test_parse_log_entry_with_no_text_or_json_payload():
    log_entry = LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.NONE,
        payload=dict(randomField="example value"),
        severity=None,
        log_name=None,
        timestamp=None,
        labels=dict(),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(
        message="Unexpected Error", data=dict(randomField="example value")
    )


def test_parse_log_entry_with_severity():
    log_entry = LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity="ERROR",
        log_name=None,
        timestamp=None,
        labels=dict(),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(message="example error", severity="ERROR")


def test_parse_log_entry_with_log_name():
    log_entry = LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name="/logs/my-log",
        timestamp=None,
        labels=dict(),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(
        message="example error", log_name="/logs/my-log"
    )


def test_parse_log_entry_with_received_timestamp():
    log_entry = LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp="2022-08-01T11:25:38.670159583Z",
        labels=dict(),
    )
    processed = process_log_entry(log_entry, APP_LOG_PAYLOAD_FACTORIES)
    assert processed == ProcessedLogEntry(
        message="example error",
        timestamp=parse("2022-08-01T12:25:38.670159583Z"),
    )