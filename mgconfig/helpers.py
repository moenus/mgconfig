import logging
from typing import Union, Any
from enum import Enum

LOGGER_NAME = "mgconf"


class Section(Enum):
    APP = "APP"
    SEC = "SEC"


class ConstSection:
    _registry: dict[str, "ConstSection"] = {}  # name -> instance

    def __new__(cls, section_handle, *args, **kwargs):
        if section_handle in cls._registry:
            return cls._registry[section_handle]  # return existing instance
        instance = super().__new__(cls)
        cls._registry[section_handle] = instance
        return instance

    def __init__(self, section_handle: str, section_prefix: str = None):
        # Prevent reinitialization if instance already exists
        if not hasattr(self, "_initialized"):
            self._section_handle = section_handle
            self._section_prefix = section_prefix
            self._initialized = True

    @property
    def section_prefix(self):
        if self._section_prefix is None:
            raise ValueError(
                f'Section prefix for {self._section_handle} is undefinded.')
        return self._section_prefix

    @section_prefix.setter
    def section_prefix(self, value):
        self._section_prefix = value

    @property
    def section_handle(self):
        return self._section_handle

    @classmethod
    def list_handles(cls):
        return [item.section_handle for item in cls._registry.values()]


section_APP = ConstSection(Section.APP, 'app')
section_SEC = ConstSection(Section.SEC, 'sec')

# test = ConstSection(Section.APP)
# print(test.section_prefix)
# print(ConstSection.list_handles())


class ConstConfig:
    _registry: dict[str, "ConstConfig"] = {}  # name -> instance

    def __new__(cls, config_handle, *args, **kwargs):
        if config_handle in cls._registry:
            return cls._registry[config_handle]  # return existing instance
        instance = super().__new__(cls)
        cls._registry[config_handle] = instance
        return instance

    def __init__(self, config_handle: str, section: ConstSection = None):
        # Prevent reinitialization if instance already exists
        if not hasattr(self, "_initialized"):
            self._config_handle = config_handle
            self._section = section
            self._config_id: str | None = None
            self._initialized = True

    @property
    def config_handle(self):
        return self._config_handle

    @property
    def config_id(self):
        if self._config_id is None and self._section is not None:
            # set a default config_id to enhance robustness
            self._config_id = f'{self._section.section_prefix}_{self._config_handle}'
        return self._config_id

    @config_id.setter
    def config_id(self, value):
        self._config_id = value

    @property
    def section_handle(self):
        return self._section_handle

    @section_handle.setter
    def section_handle(self, value):
        self._section_handle = value

    @classmethod
    def list_handles(cls):
        return [item.config_handle for item in cls._registry.values()]


config_configfile = ConstConfig('configfile', section_APP)
config_securestorefile = ConstConfig('securestore_file', section_SEC)
config_keyfile = ConstConfig('keyfile_filepath', section_SEC)
config_service_name = ConstConfig('keyring_service_name', section_SEC)

# test = ConstConfig('keyring_service_name')
# print(ConstConfig.list_config_handles())


def lazy_build_config_id(section_obj: ConstSection, config_name: str):
    return f'{section_obj.section_prefix}_{config_name}'


# class SectionPrefix:
#     """Represents a prefix for configuration sections."""

#     def __init__(self):
#         """Initialize an empty section prefix."""
#         self.prefix: Union[str, None] = None

#     def __str__(self):
#         """Return the prefix as a string.

#         Returns:
#             str: The section prefix.

#         Raises:
#             TypeError: If the prefix is undefined.
#         """
#         if self.prefix is None:
#             raise TypeError(f'Section prefix undefined.')
#         return self.prefix

#     def build_id(self, config_name: str) -> str:
#         """Build a unique identifier by combining the prefix and a config name.

#         Args:
#             config_name (str): Configuration name to append to the prefix.

#         Returns:
#             str: Combined identifier in the format '<prefix>_<config_name>'.

#         Raises:
#             ValueError: If the prefix is undefined.
#         """
#         if self.prefix is None:
#             raise ValueError("Cannot build ID: prefix undefined.")
#         return f'{self.prefix}_{config_name}'


# class ConstSections:
#     """Container for application-wide section prefixes."""
#     APP = SectionPrefix()
#     SEC = SectionPrefix()

#     @classmethod
#     def set_prefix(cls, section_handle: str, prefix: str):
#         """Set the prefix for a given section.

#         Args:
#             section_handle (str): Name of the section to modify.
#             prefix (str): Prefix string to assign.

#         Raises:
#             ValueError: If the section is not defined.
#         """
#         section = getattr(cls, section_handle, None)
#         if not isinstance(section, SectionPrefix):
#             raise ValueError(f"Section '{section_handle}' not defined.")
#         if section_handle in cls.__dict__:
#             section.prefix = prefix

#     @classmethod
#     def define(cls, section_handle: str):
#         """Define a new section dynamically.

#         Args:
#             section_handle (str): Name of the new section.

#         Raises:
#             ValueError: If a section with the same name already exists.
#         """
#         if hasattr(cls, section_handle):
#             raise ValueError(f"Section '{section_handle}' already defined.")
#         setattr(cls, section_handle, SectionPrefix())


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

    def replace_logger(self, logger: logging.Logger):
        """Replace the current logger with a custom logger instance.

        Args:
            logger (logging.Logger): New logger instance.

        Raises:
            TypeError: If the provided object is not a logging.Logger.
        """
        if not isinstance(logger, logging.Logger):
            raise TypeError("Expected a logging.Logger instance")
        self._logger = logger

    def __getattr__(self, name):
        """Delegate attribute access to the current logger.

        Args:
            name (str): Attribute name.

        Returns:
            Any: Attribute from the current logger.
        """
        return getattr(self._logger, name)


logger = LoggerWrapper()
