from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AppLogPayload:
    message: str
    data: str | Dict[str, Any]
    platform: Optional[str]
    application: Optional[str]
    log_query: Dict[str, str] = field(default_factory=dict)
    most_important_values: Optional[List[str]] = field(default=None)
