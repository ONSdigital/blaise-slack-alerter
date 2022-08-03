from lib.cloud_logging.log_entry import LogEntry, PayloadType
from lib.cloud_logging.parse_log_entry import parse_log_entry


def test_parse_log_entry_without_payload_fields():
    entry = dict(example_field="example value")
    assert parse_log_entry(entry) == LogEntry(
        resource_type=None,
        payload_type=PayloadType.NONE,
        payload=dict(example_field="example value"),
        severity=None,
        log_name=None,
        timestamp=None,
        resource_labels=dict(),
    )


def test_parse_log_entry_with_text_payload_fields():
    entry = dict(textPayload="example value")
    assert parse_log_entry(entry) == LogEntry(
        resource_type=None,
        payload_type=PayloadType.TEXT,
        payload="example value",
        severity=None,
        log_name=None,
        timestamp=None,
        resource_labels=dict(),
    )


def test_parse_log_entry_with_json_payload_fields():
    entry = dict(jsonPayload=dict(example_key="example value"))
    assert parse_log_entry(entry) == LogEntry(
        resource_type=None,
        payload_type=PayloadType.JSON,
        payload=dict(example_key="example value"),
        severity=None,
        log_name=None,
        timestamp=None,
        resource_labels=dict(),
    )


def test_parse_log_entry_with_resource_type():
    entry = parse_log_entry(
        dict(textPayload="example error", resource=dict(type="type_string"))
    )
    assert entry == LogEntry(
        resource_type="type_string",
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp=None,
        resource_labels=dict(),
    )


def test_parse_log_entry_with_resource_labels():
    entry = parse_log_entry(
        dict(
            textPayload="example error",
            resource=dict(labels=dict(label_1="value-1", label_2="value-2")),
        )
    )
    assert entry == LogEntry(
        resource_type=None,
        resource_labels=dict(label_1="value-1", label_2="value-2"),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp=None,
    )


def test_parse_log_entry_with_resource_not_a_dict():
    entry = parse_log_entry(dict(textPayload="example error", resource="resource"))
    assert entry == LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp=None,
    )


def test_parse_log_entry_with_resource_type_missing():
    entry = parse_log_entry(dict(textPayload="example error", resource=dict()))
    assert entry == LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp=None,
    )


def test_parse_log_entry_with_severity():
    entry = parse_log_entry(dict(textPayload="example error", severity="ERROR"))
    assert entry == LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity="ERROR",
        log_name=None,
        timestamp=None,
    )


def test_parse_log_entry_with_log_name():
    entry = parse_log_entry(dict(textPayload="example error", logName="/logs/my-log"))
    assert entry == LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name="/logs/my-log",
        timestamp=None,
    )


def test_parse_log_entry_with_received_timestamp():
    entry = parse_log_entry(
        dict(
            textPayload="example error",
            receiveTimestamp="2022-08-01T11:25:38.670159583Z",
        )
    )
    assert entry == LogEntry(
        resource_type=None,
        resource_labels=dict(),
        payload_type=PayloadType.TEXT,
        payload="example error",
        severity=None,
        log_name=None,
        timestamp="2022-08-01T11:25:38.670159583Z",
    )
