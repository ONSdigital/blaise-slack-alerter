import base64
import binascii
import json

from lib.cloud_functions.event import Event
from lib.cloud_functions.invalid_cloud_function_event import InvalidCloudFunctionEvent


def assert_field_in_event(field_name: str, event: dict) -> None:
    if field_name not in event:
        raise InvalidCloudFunctionEvent(f"Field '{field_name}' is missing.")


def assert_is_v1_pubsub_message(event: dict) -> None:
    if event["@type"] != "type.googleapis.com/google.pubsub.v1.PubsubMessage":
        raise InvalidCloudFunctionEvent(
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
        raise InvalidCloudFunctionEvent(
            f"Field 'data' does not contain valid base64 encoded content. {str(err)}."
        )
    except json.decoder.JSONDecodeError as err:
        raise InvalidCloudFunctionEvent(
            f"Field 'data' does not contain valid JSON. {str(err)}."
        )
