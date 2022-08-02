import base64
import json

import pytest

from lib.cloud_functions import InvalidCloudFunctionEvent, parse_event


@pytest.fixture
def event():
    return {
        "@type": "type.googleapis.com/google.pubsub.v1.PubsubMessage",
        "attributes": {
            "logging.googleapis.com/timestamp": "2022-07-22T20:36:21.891133Z"
        },
        "data": base64.b64encode(
            json.dumps(dict(value="example-json-payload")).encode("ascii")
        ),
    }


def test_parse_event_fails_when_type_does_not_exist(event):
    del event["@type"]
    with pytest.raises(InvalidCloudFunctionEvent) as e:
        parse_event(event)
    assert e.value.args[0] == "Field '@type' is missing."


def test_parse_event_fails_when_type_is_not_v1_pubsub_message(event):
    event["@type"] = "unknown"
    with pytest.raises(InvalidCloudFunctionEvent) as e:
        parse_event(event)
    assert (
        e.value.args[0]
        == "Field '@type' is 'type.googleapis.com/google.pubsub.v1.PubsubMessage'. Got 'unknown'"
    )


def test_parse_event_fails_when_data_does_not_exist(event):
    del event["data"]
    with pytest.raises(InvalidCloudFunctionEvent) as e:
        parse_event(event)
    assert e.value.args[0] == "Field 'data' is missing."


def test_parse_event_fails_when_data_is_not_valid_base64(event):
    event["data"] = "not_base_64"
    with pytest.raises(InvalidCloudFunctionEvent) as e:
        parse_event(event)
    assert e.value.args[0] == (
        "Field 'data' does not contain valid base64 encoded content. "
        "Invalid base64-encoded string: number of data characters (9) cannot be 1 more than a multiple of 4."
    )


def test_parse_event_fails_when_data_is_not_valid_json(event):
    event["data"] = base64.b64encode(b"{not-json}")
    with pytest.raises(InvalidCloudFunctionEvent) as e:
        parse_event(event)
    assert e.value.args[0] == (
        "Field 'data' does not contain valid JSON. "
        "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)."
    )


def test_parse_event_decodes_the_data(event):
    result = parse_event(event)
    assert result.data == dict(value="example-json-payload")
