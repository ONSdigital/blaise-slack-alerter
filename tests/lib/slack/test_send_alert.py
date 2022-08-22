import json

import pytest
import requests_mock

from lib.slack.send_slack_message import SlackAlertFailed, send_slack_message
from lib.slack.slack_message import SlackMessage
from lib.slack.slack_message_formatter import convert_slack_message_to_blocks


def test_successfully_sending_a_message():
    message = SlackMessage(
        title="hello world",
        fields={
            "Platform": "gce_instance",
            "Application": "bts",
        },
        content=json.dumps(
            {
                "Key1": "Test1",
                "Key2": "Test 2",
                "Key3": {"a": 1, "b": None},
            },
            indent=2,
        ),
        footnote=(
            "*Next Steps*\n"
            "1. Add some :eyes: to show you are investigating\n"
            "2. Check the system is online\n"
            "3. <http://google.com | View the logs>\n"
        ),
    )
    with requests_mock.Mocker() as mock:
        mock.post("https://slack.com/example/web-hook", text="example response")

        send_slack_message("https://slack.com/example/web-hook", message)

    assert mock.call_count is 1
    assert json.loads(mock.request_history[0].text) == convert_slack_message_to_blocks(
        message
    )


def test_error_occurred_sending_message():
    message = SlackMessage(
        title="hello world",
        fields={},
        content="",
        footnote="",
    )

    with pytest.raises(SlackAlertFailed) as err:
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://slack.com/example/web-hook",
                text="example response",
                status_code=500,
            )
            send_slack_message(
                "https://slack.com/example/web-hook",
                message,
            )

    assert err.value.args[0] == 500
    assert err.value.args[1] == "example response"
    assert err.value.args[2] == convert_slack_message_to_blocks(message)
