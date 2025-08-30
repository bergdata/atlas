"""
Utility functions and base classes for Atlas EC2 project.
Provides common functionality to reduce code duplication and improve maintainability.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any, Callable
from functools import wraps
import time
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class AtlasBase:
    """Base class providing common functionality for Atlas components."""

    def __init__(self, name: str = None):
        self.logger = logging.getLogger(name or self.__class__.__name__)
        self.name = name or self.__class__.__name__

    def log_info(self, message: str):
        """Log info message with component name."""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str, exc: Exception = None):
        """Log error message with component name."""
        if exc:
            self.logger.error(f"[{self.name}] {message}: {str(exc)}")
        else:
            self.logger.error(f"[{self.name}] {message}")

    def log_warning(self, message: str):
        """Log warning message with component name."""
        self.logger.warning(f"[{self.name}] {message}")

    def log_debug(self, message: str):
        """Log debug message with component name."""
        self.logger.debug(f"[{self.name}] {message}")

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger = logging.getLogger(func.__module__)
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}")

            raise last_exception
        return wrapper
    return decorator

@contextmanager
def timer(operation_name: str):
    """Context manager to time operations."""
    logger = logging.getLogger(__name__)
    start_time = time.time()
    logger.info(f"Starting {operation_name}...")

    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(".2f")

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary with optional default.

    Args:
        data: Dictionary to get value from
        key: Key to look for
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> tuple[bool, list]:
    """
    Validate that required fields are present in data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        Tuple of (is_valid, missing_fields)
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    return len(missing_fields) == 0, missing_fields

def format_error_message(operation: str, error: Exception, context: Dict[str, Any] = None) -> str:
    """
    Format a consistent error message.

    Args:
        operation: Name of the operation that failed
        error: The exception that occurred
        context: Additional context information

    Returns:
        Formatted error message
    """
    message = f"Operation '{operation}' failed: {str(error)}"
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        message += f" (Context: {context_str})"

    return message

class ConfigurationError(Exception):
    """Raised when there's a configuration error."""
    pass

class APIError(Exception):
    """Raised when there's an API-related error."""
    pass

class ValidationError(Exception):
    """Raised when there's a validation error."""
    pass

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        True if directory exists or was created successfully
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create directory {path}: {str(e)}")
        return False

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in MB, or 0.0 if file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with optional suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if text is truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix

class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self.cache = {}
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Any:
        """Get value from cache if not expired."""
        if key in self.cache:
            entry = self.cache[key]
            if entry['expires_at'] > time.time():
                return entry['value']
            else:
                # Remove expired entry
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL."""
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def size(self) -> int:
        """Get number of cache entries."""
        return len(self.cache)

# Global cache instance
cache = SimpleCache()
