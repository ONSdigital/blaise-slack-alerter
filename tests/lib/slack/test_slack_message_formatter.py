import json

from lib.slack.slack_message import SlackMessage
from lib.slack.slack_message_formatter import convert_slack_message_to_blocks


def test_successfully_converting_a_message_to_blocks():
    blocks = convert_slack_message_to_blocks(
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

    assert blocks == dict(
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


def test_successfully_converting_a_message_to_blocks_with_no_content():
    blocks = convert_slack_message_to_blocks(
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

    assert blocks == dict(
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
