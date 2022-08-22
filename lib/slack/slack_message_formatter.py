from lib.slack.slack_message import SlackMessage


def convert_slack_message_to_blocks(message: SlackMessage) -> dict:
    blocks = [
        dict(
            type="header",
            text=dict(type="plain_text", text=f":alert: {message.title}"),
        ),
        dict(
            type="section",
            fields=[
                dict(type="mrkdwn", text=f"*{key}:*\n{value}")
                for key, value in message.fields.items()
            ],
        ),
    ]

    if message.content != "":
        blocks.append(dict(type="divider"))
        blocks.append(
            dict(
                type="section",
                text=dict(type="plain_text", text=message.content),
            )
        )

    blocks.append(dict(type="divider"))
    blocks.append(dict(type="section", text=dict(type="mrkdwn", text=message.footnote)))

    return dict(blocks=blocks)
