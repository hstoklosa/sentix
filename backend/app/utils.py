from typing import Any
from datetime import datetime, timezone

import json

def parse_cors(v: Any) -> list[str] | str:
    """
    Parse CORS header value to string or list of strings
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

def datetime_from_timestamp(timestamp: int) -> datetime:
    """
    Convert timestamp from milliseconds to datetime object
    """
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)

def pretty_print(data: Any, suffix: str = "") -> str:
    """
    Pretty print JSON data
    """
    return print(json.dumps(data, indent=2) + suffix)
