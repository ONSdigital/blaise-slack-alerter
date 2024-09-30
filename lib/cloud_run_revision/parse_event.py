import base64
import binascii
import json

from lib.cloud_run_revision.event import Event
from lib.cloud_run_revision.invalid_cloud_run_revision_event import InvalidCloudRunRevisionEvent


def assert_field_in_event(field_name: str, event: dict) -> None:
    if field_name not in event:
        raise InvalidCloudRunRevisionEvent(f"Field '{field_name}' is missing.")


def assert_is_v1_pubsub_message(event: dict) -> None:
    if event["@type"] != "type.googleapis.com/google.pubsub.v1.PubsubMessage":
        raise InvalidCloudRunRevisionEvent(
            "Field '@type' is 'type.googleapis.com/google.pubsub.v1.PubsubMessage'. "
            f"Got '{event['@type']}'"
        )


def parse_event(event) -> Event:
    assert_field_in_event("data", event)
    assert_field_in_event("@type", event)
    assert_is_v1_pubsub_message(event)

    try:
        return Event(data=json.loads(base64.b64decode(event["data"])))
    except binascii.Error as err:
        raise InvalidCloudRunRevisionEvent(
            f"Field 'data' does not contain valid base64 encoded content. {str(err)}."
        )
    except json.decoder.JSONDecodeError as err:
        raise InvalidCloudRunRevisionEvent(
            f"Field 'data' does not contain valid JSON. {str(err)}."
        )
