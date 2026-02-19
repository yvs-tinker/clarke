"""Error types and logging bootstrap for Clarke backend services."""

from __future__ import annotations

from pathlib import Path

from loguru import logger


class ClarkeError(Exception):
    """Base exception for Clarke backend failures.

    Params:
        message (str): Human-readable error message.
    Returns:
        None: Raises an exception instance.
    """


class ConfigError(ClarkeError):
    """Raised when configuration values are missing or invalid.

    Params:
        message (str): Human-readable error message.
    Returns:
        None: Raises an exception instance.
    """


class FHIRClientError(ClarkeError):
    """Raised for FHIR retrieval and parsing failures.

    Params:
        message (str): Human-readable error message.
    Returns:
        None: Raises an exception instance.
    """


class ModelExecutionError(ClarkeError):
    """Raised when model loading or inference fails.

    Params:
        message (str): Human-readable error message.
    Returns:
        None: Raises an exception instance.
    """


class AudioError(ClarkeError):
    """Raised when audio input fails conversion or validation checks.

    Params:
        message (str): Human-readable error message.
    Returns:
        None: Raises an exception instance.
    """


def configure_logging(log_level: str = "DEBUG") -> None:
    """Configure loguru sinks for console and rotating file logs.

    Params:
        log_level (str): Minimum enabled log severity level.
    Returns:
        None: Configures global logger side effects.
    """

    Path("logs").mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(
        "logs/clarke_{time}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {extra[component]:<15} | {message}",
        rotation="50 MB",
        retention="7 days",
        level="DEBUG",
    )
    logger.add(
        sink="stderr",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {extra[component]:<15} | {message}",
        level=log_level,
    )


def get_component_logger(component: str):
    """Return a logger bound to a component name for structured logs.

    Params:
        component (str): Logical module/component identifier.
    Returns:
        loguru.Logger: Bound logger with `component` context.
    """

    return logger.bind(component=component)
