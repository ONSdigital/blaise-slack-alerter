from datetime import datetime

from lib.cloud_logging.log_query_link import create_log_query_link


def test_create_log_query_link_with_no_severities_or_fields():
    timestamp = datetime(2022, 10, 24)
    project_name = "example-project"

    link = create_log_query_link({}, [], timestamp, project_name)

    assert (
        link == f"https://console.cloud.google.com/logs/query;"
        f"query=;"
        f"cursorTimestamp=2022-10-24T00:00:00.000000Z"
        f"?referrer=search&project={project_name}"
    )


def test_create_log_query_link_with_severities_but_no_fields():
    timestamp = datetime(2022, 10, 24)
    project_name = "example-project"

    link = create_log_query_link({}, ["ERROR", "WARNING"], timestamp, project_name)

    assert (
        link == f"https://console.cloud.google.com/logs/query;"
        "query=severity%3D%28ERROR%20OR%20WARNING%29;"
        f"cursorTimestamp=2022-10-24T00:00:00.000000Z"
        f"?referrer=search&project={project_name}"
    )


def test_create_log_query_link_with_fields_but_no_severities():
    timestamp = datetime(2022, 10, 24)
    project_name = "example-project"

    link = create_log_query_link(
        {"field1": "value1", "field2": "value2"}, [], timestamp, project_name
    )

    assert (
        link == f"https://console.cloud.google.com/logs/query;"
        "query=field1%3A%22value1%22%20field2%3A%22value2%22;"
        f"cursorTimestamp=2022-10-24T00:00:00.000000Z"
        f"?referrer=search&project={project_name}"
    )


def test_create_log_query_link_with_severities_and_fields():
    timestamp = datetime(2022, 10, 24)
    project_name = "example-project"

    link = create_log_query_link(
        {"field1": "value1", "field2": "value2"},
        ["ERROR", "WARNING"],
        timestamp,
        project_name,
    )

    assert (
        link == f"https://console.cloud.google.com/logs/query;"
        "query=field1%3A%22value1%22%20field2%3A%22value2%22%20severity%3D%28ERROR%20OR%20WARNING%29;"
        f"cursorTimestamp=2022-10-24T00:00:00.000000Z"
        f"?referrer=search&project={project_name}"
    )
