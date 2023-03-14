from datetime import datetime
from typing import List, Dict
from urllib.parse import quote


def create_log_query_link(
    fields: Dict[str, str],
    severities: List[str],
    cursor_timestamp: datetime,
    project_name: str,
) -> str:
    fields_query = " ".join([f'{name}:"{value}"' for name, value in fields.items()])
    severity_query = f"severity=({' OR '.join(severities)})" if severities else ""
    query = f"{fields_query} {severity_query}".strip()
    time_stamp = cursor_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return (
        f"https://console.cloud.google.com/logs/query;"
        f"query={quote(query, safe='/@:')};"
        f"timeRange={time_stamp}%2F{time_stamp}--PT1M"
        f"?referrer=search&project={project_name}"
    )
    
