# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import logging
from typing import Union, Any
import os

LOGGER_NAME = "mgconf"
DEBUG_MARKER = "mgconfig.debug.txt"

# ------------------------------------------------------------------------------------------------------------
# config_logger
# ------------------------------------------------------------------------------------------------------------

class LoggerWrapper:
    """Wrapper around Python's logging.Logger with default console output."""

    def __init__(self):
        """Initialize the logger with a default console handler."""
        self._logger = logging.getLogger(LOGGER_NAME)
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:  # avoid duplicate handlers
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

    def replace_logger(self, logger: logging.Logger) -> None:
        """Replace the current logger with a custom logger instance.

        Args:
            logger (logging.Logger): New logger instance.

        Raises:
            TypeError: If the provided object is not a logging.Logger.
        """
        if not isinstance(logger, logging.Logger):
            raise TypeError("Expected a logging.Logger instance")
        self._logger = logger

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the current logger.

        Args:
            name (str): Attribute name.

        Returns:
            Any: Attribute from the current logger.
        """
        return getattr(self._logger, name)


config_logger = LoggerWrapper()

if not os.path.exists(DEBUG_MARKER):
    config_logger.setLevel(logging.INFO)
