import dataclasses

import pytest

from lib.cloud_logging import LogEntry, PayloadType
from lib.log_processor.log_types.audit_log import attempt_create


@pytest.fixture
def log_entry() -> LogEntry:
    return LogEntry(
        resource_type="gce_backend_service",
        resource_labels=dict(backend_service_id="2522895116060014104"),
        payload_type=PayloadType.JSON,
        payload={
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {"code": 7, "message": "Permission Denied."},
            "authenticationInfo": {},
            "requestMetadata": {
                "callerIp": "64.62.197.152",
                "callerSuppliedUserAgent": "Mozilla/5.0",
                "requestAttributes": {
                    "path": "/",
                    "host": "34.120.152.80",
                    "time": "2022-09-02T10:51:18.717071832Z",
                    "auth": {},
                },
                "destinationAttributes": {},
            },
            "serviceName": "iap.googleapis.com",
            "methodName": "AuthorizeUser",
            "authorizationInfo": [
                {
                    "resource": "projects/628324858917/iap_web/compute/services/2522895116060014104/versions/bs_0",
                    "permission": "iap.webServiceVersions.accessViaIAP",
                    "resourceAttributes": {
                        "service": "iap.googleapis.com",
                        "type": "iap.googleapis.com/WebServiceVersion",
                    },
                }
            ],
            "resourceName": "2522895116060014104",
            "request": {
                "httpRequest": {"url": "https://34.120.152.80/"},
                "@type": "type.googleapis.com/cloud.security.gatekeeper.AuthorizeUserRequest",
            },
            "metadata": {
                "device_state": "Unknown",
                "oauth_client_id": "628324858917-ldlglltgesqgn64lq22anp9grbn4p6ev.apps.googleusercontent.com",
                "device_id": "",
                "request_id": "10649173555031673437",
            },
        },
        severity="ERROR",
        log_name="/logs/cf-example",
        timestamp="2022-08-01T11:25:38.670159583Z",
    )


def test_attempt_create_succeeds_with_complete_entry(log_entry):
    instance = attempt_create(log_entry)

    assert instance is not None
    assert instance.message == "[AuditLog] Permission Denied."
    assert instance.data == log_entry.payload
    assert instance.platform == "gce_backend_service"
    assert instance.application == "[unknown]"
    assert instance.log_query == {
        "protoPayload.@type": "type.googleapis.com/google.cloud.audit.AuditLog",
    }
    assert instance.most_important_values == [
        "serviceName",
        "methodName",
        "requestMetadata.callerIp",
        "requestMetadata.callerSuppliedUserAgent",
        "requestMetadata.requestAttributes.path",
        "requestMetadata.requestAttributes.host",
        "requestMetadata.requestAttributes.time",
        "request.httpRequest.url",
    ]


def test_attempt_create_returns_none_if_payload_is_not_json(log_entry):
    instance = attempt_create(dataclasses.replace(log_entry, payload=""))
    assert instance is None


def test_attempt_create_returns_none_if_payload_type_is_missing(log_entry):
    del log_entry.payload["@type"]
    instance = attempt_create(log_entry)
    assert instance is None


def test_attempt_create_returns_none_if_payload_type_is_not_auditlog(log_entry):
    log_entry.payload.update({"@type": "not-audit-log"})
    instance = attempt_create(log_entry)
    assert instance is None
