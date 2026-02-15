"""Shared utility helpers used across backend modules."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from backend.errors import get_component_logger


def timed(component: str) -> Callable:
    """Measure function runtime and log duration with structured metadata.

    Params:
        component (str): Component name used in structured logs.
    Returns:
        Callable: Decorator wrapping the target callable.
    """

    log = get_component_logger(component)

    def decorator(func: Callable) -> Callable:
        """Wrap a function with timing instrumentation.

        Params:
            func (Callable): Function to time.
        Returns:
            Callable: Timed wrapper preserving function signature metadata.
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute wrapped function and emit success/failure timing logs.

            Params:
                *args (Any): Positional arguments passed to wrapped function.
                **kwargs (Any): Keyword arguments passed to wrapped function.
            Returns:
                Any: Original function return value.
            """

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_s = time.perf_counter() - start_time
                log.info(
                    "Function execution complete",
                    function_name=func.__name__,
                    duration_s=round(duration_s, 4),
                )
                return result
            except Exception:
                duration_s = time.perf_counter() - start_time
                log.exception(
                    "Function execution failed",
                    function_name=func.__name__,
                    duration_s=round(duration_s, 4),
                )
                raise

        return wrapper

    return decorator


def sanitize_json_payload(payload: Any) -> Any:
    """Return a JSON-serialisable deep copy of an arbitrary payload.

    Params:
        payload (Any): Input object that should be JSON serialisable.
    Returns:
        Any: Normalised payload safe for JSON transport/storage.
    """

    return json.loads(json.dumps(payload, default=str))
