from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass(frozen=True)
class AppLogPayload:
    message: str
    data: str | Dict[str, Any]
    platform: Optional[str]
    application: Optional[str]
