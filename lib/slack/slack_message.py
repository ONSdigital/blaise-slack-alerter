from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SlackMessage:
    title: str
    fields: Dict[str, str]
    content: str
    footnote: str
