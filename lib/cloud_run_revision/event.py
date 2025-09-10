from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Event:
    data: Dict[str, Any]
