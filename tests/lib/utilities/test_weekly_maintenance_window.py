import pytest
from datetime import datetime, timezone, timedelta
from typing import Any

from lib.utilities.friday_maintenance_window import is_in_friday_maintenance_window


# Test constants
FRIDAY_DATE = datetime(2025, 7, 25, 0, 0, 0, tzinfo=timezone.utc)
MAINTENANCE_START = FRIDAY_DATE.replace(hour=1, minute=25, second=0, microsecond=0)
MAINTENANCE_END = FRIDAY_DATE.replace(hour=1, minute=35, second=0, microsecond=0)
MAINTENANCE_MIDDLE = FRIDAY_DATE.replace(hour=1, minute=30, second=0, microsecond=0)


@pytest.fixture
def maintenance_friday() -> datetime:
    return MAINTENANCE_MIDDLE


@pytest.fixture
def non_maintenance_tuesday() -> datetime:
    return datetime(2025, 7, 22, 1, 30, 0, tzinfo=timezone.utc)


def create_datetime_with_offset(base_time: datetime, **kwargs: Any) -> datetime:
    return base_time.replace(**kwargs)


@pytest.mark.parametrize("invalid_input", ["not a datetime", None, 123, [], {}])
def test_returns_false_for_non_datetime_input(invalid_input: Any):
    assert is_in_friday_maintenance_window(invalid_input) is False


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (MAINTENANCE_START, True),
        (MAINTENANCE_END, True),
        (MAINTENANCE_MIDDLE, True),
        (create_datetime_with_offset(MAINTENANCE_START, minute=27), True),
        (create_datetime_with_offset(MAINTENANCE_START, minute=33), True),
    ],
)
def test_friday_maintenance_window_times(test_time: datetime, expected: bool):
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (MAINTENANCE_START.replace(minute=24), False),  # Before window (01:24)
        (MAINTENANCE_START.replace(hour=0, minute=30), False),  # Before window (00:30)
        (MAINTENANCE_END.replace(minute=36), False),  # After window (01:36)
        (MAINTENANCE_END.replace(hour=3), False),  # After window (03:35)
    ],
)
def test_friday_outside_maintenance_window(test_time: datetime, expected: bool):
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize("target_weekday", [0, 1, 2, 3, 5, 6])  # Mon-Thu, Sat-Sun
def test_non_friday_during_maintenance_hours(target_weekday: int):
    days_difference = target_weekday - 4
    non_friday = MAINTENANCE_MIDDLE + timedelta(days=days_difference)
    assert is_in_friday_maintenance_window(non_friday) is False


@pytest.mark.parametrize(
    "local_hour,local_day,tz_offset,expected",
    [
        (
            2,
            25,
            1,
            True,
        ),  # London BST: Friday 02:30+1 = Friday 01:30 UTC (within window)
        (
            21,
            24,
            -4,
            True,
        ),  # NY EDT: Thursday 21:30-4 = Friday 01:30 UTC (within window)
        (6, 25, 5, True),  # India: Friday 06:30+5 = Friday 01:30 UTC (within window)
        (1, 25, -2, False),  # Friday 01:30-2 = Friday 03:30 UTC (outside window)
    ],
)
def test_timezone_conversions(
    local_hour: int, local_day: int, tz_offset: int, expected: bool
):
    local_time = datetime(
        2025,
        7,
        local_day,
        local_hour,
        30,
        0,
        tzinfo=timezone(timedelta(hours=tz_offset)),
    )
    assert is_in_friday_maintenance_window(local_time) is expected


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (datetime(2025, 7, 25, 1, 30, 0), True),  # Naive treated as UTC
        (datetime(2025, 7, 25, 0, 30, 0), False),  # Outside window
    ],
)
def test_naive_datetime_treated_as_utc(test_time: datetime, expected: bool):
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize(
    "test_time,expected",
    [
        (MAINTENANCE_START, True),  # Exact start (01:25)
        (
            MAINTENANCE_START.replace(minute=24, second=59, microsecond=999999),
            False,
        ),  # Just before (01:24:59.999999)
        (
            MAINTENANCE_END.replace(minute=35, second=0, microsecond=1),
            False,
        ),  # Just after end (01:35:00.000001)
    ],
)
def test_edge_cases_with_microseconds(test_time: datetime, expected: bool):
    assert is_in_friday_maintenance_window(test_time) is expected


@pytest.mark.parametrize(
    "month,day",
    [
        (1, 3),  # Friday, Jan 3, 2025
        (2, 7),  # Friday, Feb 7, 2025
        (3, 14),  # Friday, Mar 14, 2025
        (12, 26),  # Friday, Dec 26, 2025
    ],
)
def test_different_friday_dates(month: int, day: int):
    friday_date = datetime(2025, month, day, 1, 30, 0, tzinfo=timezone.utc)
    assert friday_date.weekday() == 4
    assert is_in_friday_maintenance_window(friday_date) is True


@pytest.mark.parametrize(
    "month,day,expected_weekday",
    [
        (1, 4, 5),  # Saturday, Jan 4, 2025
        (2, 6, 3),  # Thursday, Feb 6, 2025
        (3, 15, 5),  # Saturday, Mar 15, 2025
        (12, 25, 3),  # Thursday, Dec 25, 2025
    ],
)
def test_different_non_friday_dates(month: int, day: int, expected_weekday: int):
    non_friday_date = datetime(2025, month, day, 1, 30, 0, tzinfo=timezone.utc)
    assert non_friday_date.weekday() == expected_weekday
    assert is_in_friday_maintenance_window(non_friday_date) is False


@pytest.mark.parametrize(
    "local_time,tz_offset,expected",
    [
        (
            datetime(2025, 7, 24, 23, 30, 0),
            -2,
            True,
        ),  # Thursday 23:30-2h = Friday 01:30 UTC
        (
            datetime(2025, 7, 25, 2, 30, 0),
            2,
            False,
        ),  # Friday 02:30+2h = Friday 00:30 UTC (outside)
        (
            datetime(2025, 7, 26, 1, 30, 0),
            1,
            False,
        ),  # Saturday 01:30+1h = Friday 00:30 UTC (outside)
    ],
)
def test_timezone_conversion_changes_weekday(
    local_time: datetime, tz_offset: int, expected: bool
):
    test_time = local_time.replace(tzinfo=timezone(timedelta(hours=tz_offset)))
    assert is_in_friday_maintenance_window(test_time) is expected


def test_fixtures_work_correctly(
    maintenance_friday: datetime, non_maintenance_tuesday: datetime
):
    assert is_in_friday_maintenance_window(maintenance_friday) is True
    assert is_in_friday_maintenance_window(non_maintenance_tuesday) is False
