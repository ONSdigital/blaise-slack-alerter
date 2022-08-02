from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class PayloadType(Enum):
    NONE = 1
    TEXT = 2
    JSON = 3


@dataclass(frozen=True)
class LogEntry:
    resource_type: Optional[str]
    payload_type: PayloadType
    payload: str | Dict[str, Any]
    severity: Optional[str]
    log_name: Optional[str]
    timestamp: Optional[str]
