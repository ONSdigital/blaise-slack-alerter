from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pytest

from lib.log_processor.processed_log_entry import ProcessedLogEntry
from lib.utilities.log_validation import (validate_gce_instance_log_entry,
                                          validate_log_entry_fields)

# Test constants
DEFAULT_TIMESTAMP = datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
DEFAULT_MESSAGE = "test message"
DEFAULT_PLATFORM = "test_platform"
DEFAULT_LOG_NAME = "test_log"
GCE_PLATFORM = "gce_instance"


def create_test_log_entry(
    message: Any = DEFAULT_MESSAGE,
    platform: Any = DEFAULT_PLATFORM,
    log_name: Any = DEFAULT_LOG_NAME,
    timestamp: Any = "USE_DEFAULT",
    **kwargs: Any
) -> ProcessedLogEntry:
    if timestamp == "USE_DEFAULT":
        timestamp = DEFAULT_TIMESTAMP

    return ProcessedLogEntry(
        message=message,
        platform=platform,
        log_name=log_name,
        timestamp=timestamp,
        **kwargs
    )


class TestValidateLogEntryFields:
    def test_returns_true_for_valid_entry_no_requirements(self) -> None:
        log_entry = create_test_log_entry()
        assert validate_log_entry_fields(log_entry) is True

    def test_returns_true_for_valid_entry_with_none_values_no_requirements(
        self,
    ) -> None:
        log_entry = ProcessedLogEntry(
            message=None, platform=None, log_name=None, timestamp=None
        )
        assert validate_log_entry_fields(log_entry) is True

    @pytest.mark.parametrize(
        "platform,required_platform,expected",
        [
            (GCE_PLATFORM, GCE_PLATFORM, True),
            ("cloud_run", GCE_PLATFORM, False),
            (None, GCE_PLATFORM, False),
            (123, GCE_PLATFORM, False),
            ("", "", True),
            ("any_platform", None, True),
            (None, None, True),
            (123, None, True),
        ],
    )
    def test_required_platform_validation(
        self, platform: Any, required_platform: Optional[str], expected: bool
    ) -> None:
        log_entry = create_test_log_entry(platform=platform)
        result = validate_log_entry_fields(
            log_entry, required_platform=required_platform
        )
        assert result is expected

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("Valid message", True),
            ("", True),
            (None, False),
            (123, False),
        ],
    )
    def test_require_message_validation(self, message: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(message=message)
        result = validate_log_entry_fields(log_entry, require_message=True)
        assert result is expected

    @pytest.mark.parametrize(
        "log_name,expected",
        [
            ("valid_log_name", True),
            ("", True),
            (None, False),
            (456, False),
        ],
    )
    def test_require_log_name_validation(self, log_name: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(log_name=log_name)
        result = validate_log_entry_fields(log_entry, require_log_name=True)
        assert result is expected

    @pytest.mark.parametrize(
        "timestamp,expected",
        [
            (DEFAULT_TIMESTAMP, True),
            (datetime(2020, 1, 1, tzinfo=timezone.utc), True),
            (77, False),
            ("2025-07-25T12:00:00Z", False),
            (None, False),
        ],
    )
    def test_require_timestamp_validation(self, timestamp: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(timestamp=timestamp)
        result = validate_log_entry_fields(log_entry, require_timestamp=True)
        assert result is expected

    def test_multiple_requirements_all_valid(self) -> None:
        log_entry = create_test_log_entry(
            message="Valid message",
            platform=GCE_PLATFORM,
            log_name="valid_log",
            timestamp=DEFAULT_TIMESTAMP,
        )
        result = validate_log_entry_fields(
            log_entry,
            required_platform=GCE_PLATFORM,
            require_message=True,
            require_log_name=True,
            require_timestamp=True,
        )
        assert result is True

    @pytest.mark.parametrize(
        "invalid_field,field_value",
        [
            ("platform", "cloud_run"),
            ("message", None),
            ("log_name", None),
            ("timestamp", "invalid"),
        ],
    )
    def test_multiple_requirements_fails_on_invalid_field(
        self, invalid_field: str, field_value: Any
    ) -> None:
        valid_data: Dict[str, Any] = {
            "message": "Valid message",
            "platform": GCE_PLATFORM,
            "log_name": "valid_log",
            "timestamp": DEFAULT_TIMESTAMP,
        }
        valid_data[invalid_field] = field_value

        log_entry = create_test_log_entry(**valid_data)
        result = validate_log_entry_fields(
            log_entry,
            required_platform=GCE_PLATFORM,
            require_message=True,
            require_log_name=True,
            require_timestamp=True,
        )
        assert result is False


class TestValidateGceInstanceLogEntry:
    @pytest.mark.parametrize(
        "platform,expected",
        [
            (GCE_PLATFORM, True),
            ("cloud_run", False),
            (None, False),
            (123, False),
        ],
    )
    def test_platform_validation(self, platform: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(platform=platform)
        result = validate_gce_instance_log_entry(log_entry)
        assert result is expected

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("Error in application", True),
            ("", True),
            (None, False),
            (123, False),
        ],
    )
    def test_message_validation(self, message: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(message=message, platform=GCE_PLATFORM)
        result = validate_gce_instance_log_entry(log_entry)
        assert result is expected

    @pytest.mark.parametrize(
        "log_name,expected",
        [
            ("projects/test-project/logs/test-log", True),
            ("", True),
            (None, False),
            (123, False),
        ],
    )
    def test_log_name_validation(self, log_name: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(log_name=log_name, platform=GCE_PLATFORM)
        result = validate_gce_instance_log_entry(log_entry)
        assert result is expected

    @pytest.mark.parametrize(
        "timestamp,expected",
        [
            (DEFAULT_TIMESTAMP, True),
            (datetime(2020, 1, 1, tzinfo=timezone.utc), True),
            (77, False),
            ("2025-07-25T12:00:00Z", False),
            (1234567890, False),
            (None, False),
        ],
    )
    def test_timestamp_validation(self, timestamp: Any, expected: bool) -> None:
        log_entry = create_test_log_entry(timestamp=timestamp, platform=GCE_PLATFORM)
        result = validate_gce_instance_log_entry(log_entry)
        assert result is expected

    def test_all_fields_invalid_returns_false(self) -> None:
        log_entry = ProcessedLogEntry(
            message=None, platform="cloud_run", log_name=None, timestamp=None
        )
        assert validate_gce_instance_log_entry(log_entry) is False

    def test_all_fields_valid_returns_true(self) -> None:
        log_entry = create_test_log_entry(
            message="Error in application",
            platform=GCE_PLATFORM,
            log_name="projects/test-project/logs/test-log",
            timestamp=DEFAULT_TIMESTAMP,
        )
        assert validate_gce_instance_log_entry(log_entry) is True

    def test_with_additional_fields_returns_true(self) -> None:
        log_entry = ProcessedLogEntry(
            message="Error in application",
            platform=GCE_PLATFORM,
            log_name="projects/test-project/logs/test-log",
            timestamp=DEFAULT_TIMESTAMP,
            severity="ERROR",
            application="test-app",
            data={"key": "value"},
        )
        assert validate_gce_instance_log_entry(log_entry) is True
