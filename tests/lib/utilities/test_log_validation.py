import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from lib.utilities.log_validation import (
    validate_log_entry_fields,
    validate_gce_instance_log_entry
)
from lib.log_processor.processed_log_entry import ProcessedLogEntry


class TestValidateLogEntryFields:
    """Test cases for the validate_log_entry_fields function."""

    def create_log_entry(
        self,
        message: str = "test message",
        platform: str = "test_platform",
        log_name: str = "test_log",
        timestamp: datetime = None,
        **kwargs
    ) -> ProcessedLogEntry:
        """Helper method to create a ProcessedLogEntry for testing."""
        if timestamp is None:
            timestamp = datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        
        return ProcessedLogEntry(
            message=message,
            platform=platform,
            log_name=log_name,
            timestamp=timestamp,
            **kwargs
        )

    def test_returns_true_for_valid_entry_no_requirements(self):
        """Test that function returns True when no specific requirements are set."""
        log_entry = self.create_log_entry()
        assert validate_log_entry_fields(log_entry) is True

    def test_returns_true_for_valid_entry_with_none_values_no_requirements(self):
        """Test that function returns True for entry with None values when no requirements are set."""
        log_entry = ProcessedLogEntry(
            message=None,
            platform=None,
            log_name=None,
            timestamp=None
        )
        assert validate_log_entry_fields(log_entry) is True

    def test_required_platform_valid(self):
        """Test validation passes when required platform matches."""
        log_entry = self.create_log_entry(platform="gce_instance")
        assert validate_log_entry_fields(log_entry, required_platform="gce_instance") is True

    def test_required_platform_invalid_mismatch(self):
        """Test validation fails when required platform doesn't match."""
        log_entry = self.create_log_entry(platform="cloud_run")
        assert validate_log_entry_fields(log_entry, required_platform="gce_instance") is False

    def test_required_platform_invalid_none(self):
        """Test validation fails when platform is None but required."""
        log_entry = self.create_log_entry(platform=None)
        assert validate_log_entry_fields(log_entry, required_platform="gce_instance") is False

    def test_required_platform_invalid_non_string(self):
        """Test validation fails when platform is not a string."""
        log_entry = self.create_log_entry(platform=123)
        assert validate_log_entry_fields(log_entry, required_platform="gce_instance") is False

    def test_require_message_valid(self):
        """Test validation passes when message is required and is a valid string."""
        log_entry = self.create_log_entry(message="Valid message")
        assert validate_log_entry_fields(log_entry, require_message=True) is True

    def test_require_message_invalid_none(self):
        """Test validation fails when message is required but is None."""
        log_entry = self.create_log_entry(message=None)
        assert validate_log_entry_fields(log_entry, require_message=True) is False

    def test_require_message_invalid_non_string(self):
        """Test validation fails when message is required but is not a string."""
        log_entry = self.create_log_entry(message=123)
        assert validate_log_entry_fields(log_entry, require_message=True) is False

    def test_require_message_invalid_empty_string(self):
        """Test validation passes when message is an empty string (still a valid string)."""
        log_entry = self.create_log_entry(message="")
        assert validate_log_entry_fields(log_entry, require_message=True) is True

    def test_require_log_name_valid(self):
        """Test validation passes when log_name is required and is a valid string."""
        log_entry = self.create_log_entry(log_name="valid_log_name")
        assert validate_log_entry_fields(log_entry, require_log_name=True) is True

    def test_require_log_name_invalid_none(self):
        """Test validation fails when log_name is required but is None."""
        log_entry = self.create_log_entry(log_name=None)
        assert validate_log_entry_fields(log_entry, require_log_name=True) is False

    def test_require_log_name_invalid_non_string(self):
        """Test validation fails when log_name is required but is not a string."""
        log_entry = self.create_log_entry(log_name=456)
        assert validate_log_entry_fields(log_entry, require_log_name=True) is False

    def test_require_timestamp_valid(self):
        """Test validation passes when timestamp is required and is a valid datetime."""
        timestamp = datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        log_entry = self.create_log_entry(timestamp=timestamp)
        assert validate_log_entry_fields(log_entry, require_timestamp=True) is True

    def test_require_timestamp_invalid_none(self):
        log_entry = self.create_log_entry(timestamp=77)
        assert validate_log_entry_fields(log_entry, require_timestamp=True) is False

    def test_require_timestamp_invalid_non_datetime(self):
        log_entry = self.create_log_entry(timestamp="2025-07-25T12:00:00Z")
        assert validate_log_entry_fields(log_entry, require_timestamp=True) is False

    def test_multiple_requirements_all_valid(self):
        log_entry = self.create_log_entry(
            message="Valid message",
            platform="gce_instance",
            log_name="valid_log",
            timestamp=datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        assert validate_log_entry_fields(
            log_entry,
            required_platform="gce_instance",
            require_message=True,
            require_log_name=True,
            require_timestamp=True
        ) is True

    def test_multiple_requirements_platform_fails_due_to_platform_mismatch(self):
        log_entry = self.create_log_entry(
            message="Valid message",
            platform="cloud_run",  
            log_name="valid_log",
            timestamp=datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        assert validate_log_entry_fields(
            log_entry,
            required_platform="gce_instance",
            require_message=True,
            require_log_name=True,
            require_timestamp=True
        ) is False

    def test_multiple_requirements_message_fails_due_to_invalid_message(self):
        log_entry = self.create_log_entry(
            message=None, 
            platform="gce_instance",
            log_name="valid_log",
            timestamp=datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        assert validate_log_entry_fields(
            log_entry,
            required_platform="gce_instance",
            require_message=True,
            require_log_name=True,
            require_timestamp=True
        ) is False

    def test_required_platform_none_allows_any_platform(self):
        log_entry_with_platform = self.create_log_entry(platform="any_platform")
        log_entry_with_none = self.create_log_entry(platform=None)
        log_entry_with_number = self.create_log_entry(platform=123)

        assert validate_log_entry_fields(log_entry_with_platform, required_platform=None) is True
        assert validate_log_entry_fields(log_entry_with_none, required_platform=None) is True
        assert validate_log_entry_fields(log_entry_with_number, required_platform=None) is True

    def test_edge_case_empty_string_platform(self):
        log_entry = self.create_log_entry(platform="")
        
        assert validate_log_entry_fields(log_entry, required_platform="") is True
        
        assert validate_log_entry_fields(log_entry, required_platform="gce_instance") is False


class TestValidateGceInstanceLogEntry:
    def create_log_entry(
        self,
        message: str = "test message",
        platform: str = "gce_instance",
        log_name: str = "test_log",
        timestamp: datetime = None,
        **kwargs
    ) -> ProcessedLogEntry:
        if timestamp is None:
            timestamp = datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        
        return ProcessedLogEntry(
            message=message,
            platform=platform,
            log_name=log_name,
            timestamp=timestamp,
            **kwargs
        )

    def test_valid_gce_instance_log_entry(self):
        log_entry = self.create_log_entry()
        assert validate_gce_instance_log_entry(log_entry) is True

    def test_invalid_platform(self):
        log_entry = self.create_log_entry(platform="cloud_run")
        assert validate_gce_instance_log_entry(log_entry) is False

        log_entry_none = self.create_log_entry(platform=None)
        assert validate_gce_instance_log_entry(log_entry_none) is False

        log_entry_number = self.create_log_entry(platform=123)
        assert validate_gce_instance_log_entry(log_entry_number) is False

    def test_invalid_message(self):
        log_entry_none = self.create_log_entry(message=None)
        assert validate_gce_instance_log_entry(log_entry_none) is False

        log_entry_number = self.create_log_entry(message=123)
        assert validate_gce_instance_log_entry(log_entry_number) is False

    def test_valid_empty_message(self):
        log_entry = self.create_log_entry(message="")
        assert validate_gce_instance_log_entry(log_entry) is True

    def test_invalid_log_name(self):
        log_entry_none = self.create_log_entry(log_name=None)
        assert validate_gce_instance_log_entry(log_entry_none) is False

        log_entry_number = self.create_log_entry(log_name=123)
        assert validate_gce_instance_log_entry(log_entry_number) is False

    def test_valid_empty_log_name(self):
        log_entry = self.create_log_entry(log_name="")
        assert validate_gce_instance_log_entry(log_entry) is True

    def test_invalid_timestamp(self):
        log_entry_none = self.create_log_entry(timestamp=77)
        assert validate_gce_instance_log_entry(log_entry_none) is False

        log_entry_string = self.create_log_entry(timestamp="2025-07-25T12:00:00Z")
        assert validate_gce_instance_log_entry(log_entry_string) is False

        log_entry_number = self.create_log_entry(timestamp=1234567890)
        assert validate_gce_instance_log_entry(log_entry_number) is False

    def test_multiple_invalid_fields(self):
        log_entry = ProcessedLogEntry(
            message=None,          
            platform="cloud_run", 
            log_name=None,         
            timestamp=None         
        )
        assert validate_gce_instance_log_entry(log_entry) is False

    def test_all_fields_present_and_valid(self):
        log_entry = self.create_log_entry(
            message="Error in application",
            platform="gce_instance",
            log_name="projects/test-project/logs/test-log",
            timestamp=datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        )
        assert validate_gce_instance_log_entry(log_entry) is True

    def test_with_additional_fields(self):
        log_entry = ProcessedLogEntry(
            message="Error in application",
            platform="gce_instance",
            log_name="projects/test-project/logs/test-log",
            timestamp=datetime(2025, 7, 25, 12, 0, 0, tzinfo=timezone.utc),
            severity="ERROR",
            application="test-app",
            data={"key": "value"}
        )
        assert validate_gce_instance_log_entry(log_entry) is True
