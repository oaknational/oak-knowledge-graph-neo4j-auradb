"""
Logging configuration for Oak Knowledge Graph pipeline.
Provides console output with optional file logging per CLAUDE.md standards.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


class PipelineLogger:
    """
    Centralized logging configuration for the Oak Knowledge Graph pipeline.
    Implements console output with optional file logging as per CLAUDE.md requirements.
    """

    def __init__(self, name: str = "oak_pipeline", level: str = "INFO"):
        """
        Initialize pipeline logger with console and optional file output.

        Args:
            name: Logger name (typically module or component name)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_console_handler()
            self._setup_file_handler()

    def _setup_console_handler(self):
        """Setup console logging handler with consistent formatting"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self):
        """Setup optional file logging handler if LOG_FILE env var is set"""
        log_file_path = os.getenv("LOG_FILE")

        if log_file_path:
            try:
                # Ensure log directory exists
                log_path = Path(log_file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                file_handler = logging.FileHandler(log_file_path, mode="a")
                file_handler.setLevel(self.level)

                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(funcName)s:%(lineno)d - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            except Exception as e:
                self.logger.warning(f"Failed to setup file logging: {e}")

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger


def get_pipeline_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for pipeline components.

    Args:
        name: Component name (e.g., 'hasura_extractor', 'csv_transformer')
        level: Optional log level override (defaults to INFO or LOG_LEVEL env var)

    Returns:
        Configured logger instance
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    pipeline_logger = PipelineLogger(name, log_level)
    return pipeline_logger.get_logger()


def setup_pipeline_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup global pipeline logging configuration.

    Args:
        level: Global logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging output

    Environment Variables:
        LOG_LEVEL: Override default logging level
        LOG_FILE: Enable file logging to specified path
    """
    # Set environment variables for consistent configuration
    os.environ["LOG_LEVEL"] = level.upper()
    if log_file:
        os.environ["LOG_FILE"] = log_file

    # Configure root logger to prevent duplicate messages
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


def log_pipeline_stage(logger: logging.Logger, stage: str, status: str = "START"):
    """
    Log pipeline stage transitions with consistent formatting.

    Args:
        logger: Logger instance
        stage: Pipeline stage name (e.g., 'EXTRACTION', 'TRANSFORMATION')
        status: Stage status (START, COMPLETE, ERROR)
    """
    separator = "=" * 50
    if status == "START":
        logger.info(f"\n{separator}")
        logger.info(f"PIPELINE STAGE: {stage} - {status}")
        logger.info(f"{separator}")
    elif status == "COMPLETE":
        logger.info(f"PIPELINE STAGE: {stage} - {status} ✅")
        logger.info(f"{separator}\n")
    elif status == "ERROR":
        logger.error(f"PIPELINE STAGE: {stage} - {status} ❌")
        logger.error(f"{separator}\n")


def log_data_operation(
    logger: logging.Logger, operation: str, count: int, entity_type: str = "records"
):
    """
    Log data operations with consistent formatting for counts and types.

    Args:
        logger: Logger instance
        operation: Operation description (e.g., 'Extracted', 'Validated', 'Transformed')
        count: Number of items processed
        entity_type: Type of entities (records, nodes, relationships)
    """
    logger.info(f"{operation}: {count:,} {entity_type}")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str,
    identifiers: Optional[dict] = None,
):
    """
    Log errors with context and identifiers as per CLAUDE.md requirements.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Context description (e.g., 'Hasura API call', 'CSV generation')
        identifiers: Optional dict of relevant identifiers (view_name, field_name, etc.)
    """
    error_msg = f"Error in {context}: {str(error)}"

    if identifiers:
        identifier_str = ", ".join(f"{k}={v}" for k, v in identifiers.items())
        error_msg += f" [{identifier_str}]"

    logger.error(error_msg)

    # Log full traceback in debug mode
    logger.debug("Full traceback:", exc_info=True)
