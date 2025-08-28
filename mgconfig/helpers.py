# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import threading
import logging
from typing import Union, Any
from enum import Enum

LOGGER_NAME = "mgconf"


# ------------------------------------------------------------------------------------------------------------
# Section(Enum), ConstSection, ConstConfig, lazy_build_config_id and pseudo constants
# ------------------------------------------------------------------------------------------------------------

class Section(Enum):
    """Enumeration of supported configuration sections."""
    APP = "APP"
    SEC = "SEC"


class ConstSection:
    """Represents a constant configuration section (singleton per handle)."""
    _registry: dict[str, "ConstSection"] = {}  # name -> instance

    def __new__(cls, section_handle, *args, **kwargs):
        """Ensure only one instance exists per section handle.

        Args:
            section_handle (str): Unique identifier for the section.

        Returns:
            ConstSection: Existing or newly created instance.
        """
        if section_handle in cls._registry:
            return cls._registry[section_handle]  # return existing instance
        instance = super().__new__(cls)
        cls._registry[section_handle] = instance
        return instance

    def __init__(self, section_handle: str, section_prefix: str = None):
        """Initialize a section with a handle and optional prefix.

        Args:
            section_handle (str): Unique identifier for the section.
            section_prefix (str, optional): String prefix used in config IDs.
        """
        if not hasattr(self, "_initialized"):
            self._section_handle = section_handle
            self._section_prefix = section_prefix
            self._initialized = True

    @property
    def section_prefix(self) -> str:
        """Return the section prefix.

        Returns:
            str: The prefix string.

        Raises:
            ValueError: If the section prefix is not defined.
        """
        if self._section_prefix is None:
            raise ValueError(
                f'Section prefix for {self._section_handle} is undefinded.')
        return self._section_prefix

    @section_prefix.setter
    def section_prefix(self, value: str):
        """Set the section prefix.

        Args:
            value (str): Prefix string to set.
        """
        self._section_prefix = value

    @property
    def section_handle(self) -> str:
        """Return the section handle.

        Returns:
            str: The section handle.
        """
        return self._section_handle

    @classmethod
    def list_handles(cls) -> list[str]:
        """List all registered section handles.

        Returns:
            list[str]: List of section handle strings.
        """

        return [item.section_handle for item in cls._registry.values()]


section_APP = ConstSection(Section.APP, 'app')
section_SEC = ConstSection(Section.SEC, 'sec')


class ConstConfig:
    """Represents a constant configuration key (singleton per handle)."""
    _registry: dict[str, "ConstConfig"] = {}  # name -> instance

    def __new__(cls, config_handle, *args, **kwargs):
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

    def __init__(self, config_handle: str, section: ConstSection = None):
        """Initialize a config constant.

        Args:
            config_handle (str): Unique identifier for the config entry.
            section (ConstSection, optional): Associated configuration section.
        """

        # Prevent reinitialization if instance already exists
        if not hasattr(self, "_initialized"):
            self._config_handle = config_handle
            self._section = section
            self._config_id: str | None = None
            self._initialized = True

    @property
    def config_handle(self) -> str:
        """Return the config handle.

        Returns:
            str: The config handle string.
        """
        return self._config_handle

    @property
    def config_id(self) -> str:
        """Return or lazily build the config ID.

        Returns:
            str | None: Config ID string, or None if no section is set.
        """
        if self._config_id is None and self._section is not None:
            # set a default config_id to enhance robustness
            self._config_id = f'{self._section.section_prefix}_{self._config_handle}'
        return self._config_id

    @config_id.setter
    def config_id(self, value: str):
        """Manually override the config ID.

        Args:
            value (str): New config ID value.
        """
        self._config_id = value

    # @property
    # def section_handle(self):
    #     return self._section_handle

    # @section_handle.setter
    # def section_handle(self, value):
    #     self._section_handle = value

    @classmethod
    def list_handles(cls) -> list[str]:
        """List all registered config handles.

        Returns:
            list[str]: List of config handle strings.
        """
        return [item.config_handle for item in cls._registry.values()]


config_configfile = ConstConfig('configfile', section_APP)
config_securestorefile = ConstConfig('securestore_file', section_SEC)
config_keyfile = ConstConfig('keyfile_filepath', section_SEC)
config_service_name = ConstConfig('keyring_service_name', section_SEC)


def lazy_build_config_id(section_obj: ConstSection, config_name: str) -> str:
    """Build a config ID from a section and config name.

    Args:
        section_obj (ConstSection): Section to use.
        config_name (str): Name of the config key.

    Returns:
        str: Combined config ID string.
    """    
    return f'{section_obj.section_prefix}_{config_name}'

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
