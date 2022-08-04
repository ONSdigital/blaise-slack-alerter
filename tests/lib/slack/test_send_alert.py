import json

import pytest
import requests_mock

from lib.slack.send_slack_message import SlackAlertFailed, send_slack_message
from lib.slack.slack_message import SlackMessage


def test_successfully_sending_a_message():
    with requests_mock.Mocker() as mock:
        mock.post("https://slack.com/example/web-hook", text="example response")
        send_slack_message(
            "https://slack.com/example/web-hook",
            SlackMessage(
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
            ),
        )

    assert mock.call_count is 1
    assert json.loads(mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text=dict(text=":alert: hello world", type="plain_text"),
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\ngce_instance", type="mrkdwn"),
                    dict(text="*Application:*\nbts", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text="{\n"
                    '  "Key1": "Test1",\n'
                    '  "Key2": "Test 2",\n'
                    '  "Key3": {\n'
                    '    "a": 1,\n'
                    '    "b": null\n'
                    "  }\n"
                    "}",
                    type="plain_text",
                ),
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text="*Next Steps*\n"
                    "1. Add some :eyes: to show you are "
                    "investigating\n"
                    "2. Check the system is online\n"
                    "3. <http://google.com | View the logs>\n",
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )


def test_successfully_sending_a_message_with_no_content():
    with requests_mock.Mocker() as mock:
        mock.post("https://slack.com/example/web-hook", text="example response")
        send_slack_message(
            "https://slack.com/example/web-hook",
            SlackMessage(
                title="hello world",
                fields={
                    "Platform": "gce_instance",
                    "Application": "bts",
                },
                content="",
                footnote=(
                    "*Next Steps*\n"
                    "1. Add some :eyes: to show you are investigating\n"
                    "2. Check the system is online\n"
                    "3. <http://google.com | View the logs>\n"
                ),
            ),
        )

    assert mock.call_count is 1
    assert json.loads(mock.request_history[0].text) == dict(
        blocks=[
            dict(
                text=dict(text=":alert: hello world", type="plain_text"),
                type="header",
            ),
            dict(
                fields=[
                    dict(text="*Platform:*\ngce_instance", type="mrkdwn"),
                    dict(text="*Application:*\nbts", type="mrkdwn"),
                ],
                type="section",
            ),
            dict(type="divider"),
            dict(
                text=dict(
                    text="*Next Steps*\n"
                    "1. Add some :eyes: to show you are "
                    "investigating\n"
                    "2. Check the system is online\n"
                    "3. <http://google.com | View the logs>\n",
                    type="mrkdwn",
                ),
                type="section",
            ),
        ]
    )


def test_error_occurred_sending_message():
    with pytest.raises(SlackAlertFailed) as err:
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://slack.com/example/web-hook",
                text="example response",
                status_code=500,
            )
            send_slack_message(
                "https://slack.com/example/web-hook",
                SlackMessage(
                    title="hello world",
                    fields={},
                    content="",
                    footnote="",
                ),
            )

    assert err.value.args[0] == 500
    assert err.value.args[1] == "example response"
    assert err.value.args[2] == dict(
        blocks=[
            dict(
                text=dict(text=":alert: hello world", type="plain_text"), type="header"
            ),
            dict(fields=[], type="section"),
            dict(type="divider"),
            dict(text=dict(text="", type="mrkdwn"), type="section"),
        ]
    )
