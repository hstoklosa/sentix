from typing import Any
from datetime import datetime, timezone

import sys
import logging
import json


def setup_logger():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS header value to string or list of strings"""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


def datetime_from_timestamp(timestamp: int) -> datetime:
    """
    Convert timestamp from milliseconds to UTC datetime object with 
    explicit timezone information.
    
    Args:
        timestamp: Unix timestamp in milliseconds
        
    Returns:
        datetime: UTC datetime object with timezone info
    """
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def format_datetime_iso(dt: datetime) -> str:
    """
    Format a datetime object to ISO 8601 format with explicit UTC timezone, 
    ensuring it has timezone information before formatting.
    
    Args:
        dt: Datetime object, with or without timezone info
        
    Returns:
        str: ISO 8601 formatted datetime string with explicit 'Z' UTC indicator
    """
    # Ensure datetime has timezone info, defaulting to UTC if none
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Format to ISO 8601 with 'Z' indicator for UTC
    return dt.isoformat().replace('+00:00', 'Z')


def pretty_print(data: Any, suffix: str = "") -> str:
    """
    Pretty print JSON data
    """
    return print(json.dumps(data, indent=2) + suffix)
