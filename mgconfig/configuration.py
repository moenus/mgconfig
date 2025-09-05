# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from .config_defs import ConfigDefs
from .config_types import SECRET_TYPE
from .config_items import config_items, config_items_new
from .config_item_handler import ConfigItem, ConfigItemHandler
from .extension_system import PostProcessing
from typing import Any, Dict, Mapping, Sequence, Optional, Union
from .helpers import config_logger
from .singleton_meta import SingletonMeta
from types import MappingProxyType


class Configuration(metaclass=SingletonMeta):
    """
    Singleton representing application configuration values.

    Configuration values are loaded from environment variables and JSON configuration
    files. If a value is not found in these sources, a default from the configuration
    definitions is used. Configuration items are accessible via attribute-style access
    or dictionary-like access.
    """

    _values: Dict[str, Any]
    _initialized: bool

    def __init__(self, cfg_defs_filepaths: Union[str, Sequence[str]] = None) -> None:
        """
        Initialize the configuration singleton.

        Args:
            cfg_defs_filepaths (Union[str, List[str]], optional): Path or list of
                paths to configuration definition files.

        Raises:
            TypeError: If `cfg_defs_filepaths` is not provided on first initialization.
        """
        if self._initialized:
            return  # avoid re-initializing
        self._initialized = True
        self._values = {}

        if cfg_defs_filepaths is None:
            raise TypeError('Missing configuration definition filepath(s).')
        ConfigDefs(cfg_defs_filepaths)
        ConfigItemHandler.build()

        for config_id, config_value in config_items.items():
            self.set_property_value(config_id, config_value.value)

        # call provided post processing functions
        for pp_func in PostProcessing().dict.values():
            try:
                pp_func(self)
            except Exception as e:
                config_logger.error(
                    f"Post processing function {pp_func.__name__} failed: {e}")

    def get_value(self, config_id: str, fail_on_error: bool = False) -> Any:
        """
        Retrieve the current value of a configuration item.

        Args:
            config_id (str): The configuration identifier.
            fail_on_error (bool, optional): Whether to raise an error if the
                value is not found. Defaults to False.

        Returns:
            Any: The configuration value, or None if not found and `fail_on_error` is False.

        Raises:
            ValueError: If the configuration ID is not found and `fail_on_error` is True.
        """
        if config_id in self._values:
            return self._values[config_id]

        if fail_on_error:
            raise ValueError(f'Configuration value {config_id} not found.')
        else:
            return None

    def get_config_item(self, config_id: str, fail_on_error: bool = True) -> Optional[ConfigItem]:
        """
        Retrieve the ConfigItem object associated with a configuration ID.

        Args:
            config_id (str): The configuration identifier.
            fail_on_error (bool, optional): Whether to raise an error if the item is
                not found. Defaults to True.

        Returns:
            Optional[ConfigItem]: The ConfigItem object if found, or None if `fail_on_error` is False.

        Raises:
            ValueError: If the configuration ID is not found and `fail_on_error` is True.
        """
        if config_id in config_items:
            return config_items.get(config_id)
        if not fail_on_error:
            return None
        raise ValueError(f'Configuration value {config_id} not found.')

    def __getitem__(self, config_id: str) -> Any:
        """
        Retrieve a configuration value using dictionary-like syntax.

        Args:
            config_id (str): The configuration identifier.

        Returns:
            Any: The configuration value.

        Raises:
            ValueError: If the configuration ID is not found.
        """
        return self.get_value(config_id, fail_on_error=True)

    def __getattr__(self, name) -> Any:
        """
        Provide attribute-style access to configuration values.

        Args:
            name (str): The configuration identifier.

        Returns:
            Any: The configuration value.

        Raises:
            AttributeError: If the configuration value or internal attribute does not exist.
        """
        if name in ("_values", "_initialized"):
            raise AttributeError(
                f"{self.__class__.__name__} has no attribute {name}")
        _values = self.__dict__.get("_values", {})
        if name in _values:
            return _values[name]
        raise AttributeError(
            f"{self.__class__.__name__} has no attribute {name}")

    def __contains__(self, config_id: str) -> bool:
        """
        Check whether a configuration value exists.

        Args:
            config_id (str): The configuration identifier.

        Returns:
            bool: True if the configuration exists, False otherwise.
        """
        return config_id in self._values

    @property
    def data_rows(self) -> Sequence[Mapping[str, Any]]:
        """
        Return all configuration values and their metadata as rows.

        Each row contains metadata and the current value of a configuration item.
        If a pending new value exists, it is included as a separate row.

        Returns:
            List[Dict[str, Any]]: List of dictionaries representing configuration items.
        """
        rows: Sequence[Dict[str, Any]] = []
        for config_id, config_value in config_items.items():
            rows.append(config_value.get_display_dict())
            if config_id in config_items_new:
                new_config_value = config_items_new[config_id]
                rows.append(new_config_value.get_display_dict())
        return rows

    def to_dict(self) -> Mapping[str, Any]:
        """
        Return a dictionary of all current configuration values.

        Returns:
            Mapping[str, Any]: Dictionary mapping configuration IDs to their current values.
        """
        return MappingProxyType(self._values)

    def save_new_value(self, config_id: str, new_value: Any, apply_immediately: bool = False) -> bool:
        """
        Save a new configuration value to the underlying store.

        Args:
            config_id (str): The configuration identifier.
            new_value (Any): The new value to save.
            apply_immediately (bool, optional): Whether to apply the value immediately
                to the current instance. Defaults to False. Values of secret type
                are always applied immediately.

        Returns:
            bool: True if the value was saved successfully, False otherwise.
        """
        config_item = self.get_config_item(config_id, fail_on_error=True)
        if config_item.config_type == SECRET_TYPE:
            apply_immediately = True
        result = ConfigItemHandler.save_new_value(
            config_id, new_value, apply_immediately)
        if result and apply_immediately:
            self.set_property_value(config_id, new_value)
        return result

    def set_property_value(self, name: str, value: Any) -> None:
        """
        Set or add a configuration value in the internal namespace.

        Args:
            name (str): The configuration identifier.
            value (Any): The value to assign.
        """
        self._values[name] = value
