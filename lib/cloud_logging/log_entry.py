from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union


class PayloadType(Enum):
    NONE = 1
    TEXT = 2
    JSON = 3


@dataclass(frozen=True)
class LogEntry:
    resource_type: Optional[str]
    resource_labels: Dict[str, str]
    labels: Dict[str, str]
    payload_type: PayloadType
    payload: Union[str, Dict[str, Any]]
    severity: Optional[str]
    log_name: Optional[str]
    timestamp: Optional[str]
