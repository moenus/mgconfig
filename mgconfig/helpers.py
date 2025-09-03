# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import threading
import logging
from typing import Union, Any
from enum import Enum

LOGGER_NAME = "mgconf"


# ------------------------------------------------------------------------------------------------------------
# ConstConfig, lazy_build_config_id and pseudo constants
# ------------------------------------------------------------------------------------------------------------

APP = 'app'
SEC = 'sec'


class ConfigKeyMap:
    """Represents a constant configuration key (singleton per handle)."""
    _registry: dict[str, "ConfigKeyMap"] = {}  # name -> instance

    def __new__(cls, section_prefix: str, config_handle, *args, **kwargs):
        """Ensure only one instance exists per config handle.

        Args:
            config_handle (str): Unique identifier for the config.

        Returns:
            ConstConfig: Existing or newly created instance.
        """
        if config_handle in cls._registry:
            return cls._registry[config_handle]  # return existing instance
        instance = super().__new__(cls)
        cls._registry[config_handle] = instance
        return instance

    def __init__(self, section_prefix: str,  config_handle: str):
        """Initialize a config constant.

        Args:
            config_handle (str): Unique identifier for the config entry.
            section (ConstSection, optional): Associated configuration section.
        """

        # Prevent reinitialization if instance already exists
        if not hasattr(self, "_initialized"):
            self._config_handle = config_handle
            self.config_name = config_handle
            self.section_prefix = section_prefix
            self._initialized = True

    @property
    def id(self) -> str:
        """Return or lazily build the config ID.

        Returns:
            str | None: Config ID string, or None if no section is set.
        """
        return self.section_prefix + '_' + self.config_name

    @classmethod
    def list_handles(cls) -> list[str]:
        """List all registered config handles.

        Returns:
            list[str]: List of config handle strings.
        """
        return [item.config_handle for item in cls._registry.values()]


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

# ------------------------------------------------------------------------------------------------------------
# SingletonMeta
# ------------------------------------------------------------------------------------------------------------


class SingletonMeta(type):
    """Thread-safe metaclass for implementing the Singleton pattern."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Return the singleton instance, creating it if necessary.

        Args:
            *args: Positional arguments for instance initialization.
            **kwargs: Keyword arguments for instance initialization.

        Returns:
            object: Singleton instance of the class.
        """
        # attach a per-class lock lazily
        lock = getattr(cls, "_lock", None)
        if lock is None:
            lock = threading.RLock()
            setattr(cls, "_lock", lock)

        if cls in SingletonMeta._instances:
            return SingletonMeta._instances[cls]

        with lock:
            # double-check inside lock
            if cls in SingletonMeta._instances:
                return SingletonMeta._instances[cls]

            # 🔑 Create instance *outside the lock* to avoid deadlocks
            instance = super().__call__(*args, **kwargs)

            SingletonMeta._instances[cls] = instance
            return instance

    def reset_instance(cls) -> None:
        """Reset the singleton instance for this class.

        Removes the instance from the registry, so a new one will be created
        on the next instantiation.
        """
        """Reset the singleton instance for this class."""
        lock = getattr(cls, "_lock", None)
        if lock is None:
            return
        with lock:
            if cls in SingletonMeta._instances:
                del SingletonMeta._instances[cls]
