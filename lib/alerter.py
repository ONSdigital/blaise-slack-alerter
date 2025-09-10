from typing import Any, Protocol, TypeVar

from lib.log_processor import ProcessedLogEntry

Alert = TypeVar("Alert")


class Alerter(Protocol[Alert]):
    def send_alert(self, message: Alert) -> None:
        raise NotImplementedError()

    def create_raw_alert(self, raw: Any) -> Alert:
        raise NotImplementedError()

    def create_alert(self, entry: ProcessedLogEntry) -> Alert:
        raise NotImplementedError()
