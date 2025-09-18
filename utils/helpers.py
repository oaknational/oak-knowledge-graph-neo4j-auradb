"""
Shared utility functions for Oak Knowledge Graph pipeline.
Provides common operations used across pipeline components.
"""

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Union
from datetime import datetime


def safe_filename(name: str, max_length: int = 100) -> str:
    """
    Create a safe filename from a string by removing invalid characters.

    Args:
        name: Original string to convert to filename
        max_length: Maximum filename length (default 100)

    Returns:
        Safe filename string
    """
    # Remove invalid characters and replace with underscores
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
    # Remove multiple consecutive underscores
    safe_name = re.sub(r"_+", "_", safe_name)
    # Strip leading/trailing underscores and whitespace
    safe_name = safe_name.strip("_").strip()
    # Limit length
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip("_")
    return safe_name or "unnamed"


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path to create

    Returns:
        Path object for the created directory

    Raises:
        OSError: If directory cannot be created
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def load_json_with_env_substitution(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON file with environment variable substitution.
    Replaces ${VAR_NAME} placeholders with environment variable values.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded JSON data with environment variables substituted

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        ValueError: If required environment variable is missing
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all environment variable placeholders
    env_vars = re.findall(r"\$\{([^}]+)\}", content)

    # Substitute environment variables
    for var_name in env_vars:
        env_value = os.getenv(var_name)
        if env_value is None:
            raise ValueError(f"Required environment variable '{var_name}' not found")
        content = content.replace(f"${{{var_name}}}", env_value)

    return json.loads(content)


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique ID for Neo4j import operations.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string suitable for Neo4j import
    """
    unique_part = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}{unique_part}" if prefix else unique_part


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunked sublists
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def validate_required_env_vars(required_vars: List[str]) -> Dict[str, str]:
    """
    Validate that all required environment variables are set.

    Args:
        required_vars: List of required environment variable names

    Returns:
        Dict of variable names to values

    Raises:
        ValueError: If any required variables are missing
    """
    missing_vars = []
    env_values = {}

    for var_name in required_vars:
        value = os.getenv(var_name)
        if value is None:
            missing_vars.append(var_name)
        else:
            env_values[var_name] = value

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return env_values


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB", "532 KB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1m 23s", "45.2s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.1f}s"

    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information.

    Args:
        file_path: Path to file

    Returns:
        Dict with file information (size, modified time, etc.)
    """
    path = Path(file_path)

    if not path.exists():
        return {"exists": False}

    stat = path.stat()
    return {
        "exists": True,
        "size_bytes": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_file": path.is_file(),
        "is_directory": path.is_dir(),
        "name": path.name,
        "stem": path.stem,
        "suffix": path.suffix,
    }


def sanitize_dict_for_logging(
    data: Dict[str, Any], max_length: int = 100
) -> Dict[str, Any]:
    """
    Sanitize dictionary for safe logging by truncating long values.

    Args:
        data: Dictionary to sanitize
        max_length: Maximum length for string values

    Returns:
        Sanitized dictionary safe for logging
    """
    sanitized = {}

    for key, value in data.items():
        if isinstance(value, str) and len(value) > max_length:
            sanitized[key] = f"{value[:max_length]}... (truncated)"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_for_logging(value, max_length)
        elif isinstance(value, list) and len(value) > 5:
            sanitized[key] = f"[{len(value)} items] {value[:2]}...{value[-1:]}"
        else:
            sanitized[key] = value

    return sanitized


def validate_neo4j_identifier(identifier: str) -> bool:
    """
    Validate Neo4j identifier (node label, relationship type, property name).

    Args:
        identifier: Identifier to validate

    Returns:
        True if identifier is valid for Neo4j
    """
    # Neo4j identifiers must start with letter/underscore and contain only
    # alphanumeric/underscore
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    return bool(re.match(pattern, identifier))


def create_data_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a summary of data for logging and validation.

    Args:
        data: List of data records

    Returns:
        Summary statistics and information
    """
    if not data:
        return {"record_count": 0, "fields": [], "sample_record": None}

    # Get all unique fields across records
    all_fields = set()
    for record in data:
        all_fields.update(record.keys())

    # Create field type analysis
    field_types = {}
    for field in all_fields:
        types_seen = set()
        for record in data:
            if field in record and record[field] is not None:
                types_seen.add(type(record[field]).__name__)
        field_types[field] = list(types_seen)

    return {
        "record_count": len(data),
        "fields": sorted(all_fields),
        "field_types": field_types,
        "sample_record": sanitize_dict_for_logging(data[0]) if data else None,
    }
