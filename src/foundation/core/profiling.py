import functools
import time
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

def timing_profile(func: F) -> F:
    """
    Decorator that logs the execution time of a function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Log with extra fields for JSON logger
        logger.info(
            "Execution profile: %s took %.4f seconds",
            func.__qualname__,
            duration,
            extra={"extra_fields": {
                "profile": {
                    "function": func.__qualname__,
                    "duration_seconds": duration
                }
            }}
        )
        return result
    return wrapper  # type: ignore
