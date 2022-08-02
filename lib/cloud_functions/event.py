from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class Event:
    data: Dict[str, Any]
