from datetime import datetime
from typing import List, Dict


def create_log_query_link(
    fields: Dict[str, str],
    severities: List[str],
    cursor_timestamp: datetime,
    project_name: str,
) -> str:
    query = " ".join(
        [
            " ".join([f'{name}:"{value}"' for name, value in fields.items()]),
            " OR ".join([f'severity:"{severity}"' for severity in severities]),
        ]
    ).strip()

    return (
        f"https://console.cloud.google.com/logs/query;"
        f"query={_encode_spaces(query)};"
        f"cursorTimestamp={cursor_timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"
        f"?referrer=search&project={project_name}"
    )


def _encode_spaces(input: str) -> str:
    return input.replace(" ", "%20")
