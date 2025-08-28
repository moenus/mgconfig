# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from .config_defs import ConfigDefs, ConfigDef
from .config_values import config_values, config_values_new
from .config_value_handler import ConfigValue, ConfigValueHandler
from .extension_system import PostProcessing
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from types import SimpleNamespace
from .helpers import SingletonMeta


class Configuration(metaclass=SingletonMeta):
    """ Reperesents the configuration values defined in environment variables 
        and a json configuration file. 
        If a value is not found in these sources a default value from the configuration definitions is used.
    """
    __slots__ = ("_initialized", "extended", "__dict__")

    def __init__(self, cfg_defs_filepaths: Union[str, List[str]] = None):
        """Initialize the configuration singleton.

        Args:
            cfg_defs_filepaths (Union[str, List[str]], optional): Path or list of
                paths to configuration definition files.

        Raises:
            TypeError: If `cfg_defs_filepaths` is not provided on first initialization.
        """        
        if hasattr(self, "_initialized"):  # avoid re-initializing
            return
        if cfg_defs_filepaths is None:
            raise TypeError(f'Missing configuration definition filepath(s).')
        self._initialized = True
        ConfigDefs(cfg_defs_filepaths)
        ConfigValueHandler.build()
        self.extended = SimpleNamespace()

        for config_id, config_value in config_values.items():
             setattr(self, config_id, config_value.value)
        del config_value  #optimization to drop the object before function exit.

        # call provided post processing functions
        for pp_func in PostProcessing().dict.values():
            try:
                pp_func(self)
            except:
                pass    
        return

    def get_value(self, config_id: str, fail_on_error: bool = False) -> Any:
        """Retrieve the current value of a configuration item.

        Args:
            config_id (str): The configuration identifier.
            fail_on_error (bool, optional): Whether to raise an error if the
                value is not found. Defaults to False.

        Returns:
            Any: The configuration value, or None if not found and
            `fail_on_error` is False.

        Raises:
            ValueError: If the configuration ID is not found and
            `fail_on_error` is True.
        """
        if config_id in self.__dict__:
            return self.__dict__[config_id]
        if fail_on_error:
            raise ValueError(f'Configuration value {config_id} not found.')
        else:
            return None

    def get_config_object(self, config_id: str, fail_on_error: bool = True) -> ConfigValue:
        """Retrieve the `ConfigValue` object associated with a configuration ID.

        Args:
            config_id (str): The configuration identifier.
            fail_on_error (bool, optional): Whether to raise an error if the
                object is not found. Defaults to True.

        Returns:
            ConfigValue: The configuration value object.

        Raises:
            ValueError: If the configuration ID is not found and
            `fail_on_error` is True.
        """
        if config_id in config_values:
            return config_values.get(config_id)
        if fail_on_error:
            raise ValueError(f'Configuration value {config_id} not found.')

    def __getitem__(self, config_id: str) -> Any:
        """Retrieve a configuration value using dictionary-like syntax.

        Args:
            config_id (str): The configuration identifier.

        Returns:
            Any: The configuration value.

        Raises:
            ValueError: If the configuration ID is not found.
        """        
        return self.get_value(config_id, fail_on_error=True)

    def __contains__(self, config_id: str) -> bool:
        """Check whether a configuration value exists.

        Args:
            config_id (str): The configuration identifier.

        Returns:
            bool: True if the configuration exists, False otherwise.
        """
        return config_id in self.__dict__

    @property
    def data_rows(self) -> List[List[Any]]:
        """Return all configuration values and their metadata as rows.

        Returns:
            List[List[Any]]: A list of rows, where each row contains
            configuration metadata and values, including both current
            and pending (new) values.
        """
        rows = []
        for config_id, config_value in config_values.items():
            rows.append(self._get_config_row(config_value.cfg_def,
                        str(config_value), config_value.source))
            if config_id in config_values_new:
                rows.append(self._get_config_row(config_value.cfg_def, str(
                    config_values_new.get(config_id)), "new"))
        return rows

    def save_new_value(self, config_id: str, new_value: Any, apply_immediately: bool = False) -> bool:
        """Save a new configuration value to the underlying store.

        Args:
            config_id (str): The configuration identifier.
            new_value (Any): The new value to save.
            apply_immediately (bool, optional): Whether to apply the value
                immediately to the current instance. Defaults to False.
                Secrets are always applied immediately.

        Returns:
            bool: True if the value was saved successfully, False otherwise.
        """
        if self.get_config_object(config_id).config_type == "secret":
            apply_immediately = True
        result = ConfigValueHandler.save_new_value(
            config_id, new_value, apply_immediately)
        if result and apply_immediately:
            self._set_property(config_id, new_value)
        return result

    def set_extended_item(self, name: str, value: Any) -> None:
        """Set or add an attribute in the `extended` namespace.

        Args:
            name (str): The attribute name.
            value (Any): The value to assign to the attribute.
        """
        setattr(self.extended, name, value)

    def extended_item_exists(self, name: str) -> bool:
        """Check whether an attribute exists in the `extended` namespace.

        Args:
            name (str): The attribute name.

        Returns:
            bool: True if the attribute exists, False otherwise.
        """
        return hasattr(self.extended, name)

    def get_extended_item(self, name: str) -> Any:
        """Retrieve an attribute from the `extended` namespace.

        Args:
            name (str): The attribute name.

        Returns:
            Any: The attribute value, or None if it does not exist.
        """
        return getattr(self.extended, name, None)

    @staticmethod
    def _get_config_row(config_def: ConfigDef, value_str: str, source: str) -> List[Any]:
        """Build a row representing a configuration value and metadata.

        Args:
            config_def (ConfigDef): The configuration definition object.
            value_str (str): The string representation of the value.
            source (str): The source of the value (e.g., "env", "file", "new").

        Returns:
            List[Any]: A row containing configuration metadata and value.
        """        
        return [
            config_def.config_section,
            config_def.config_name,
            config_def.config_env or '',
            config_def.config_default or '',
            str(source),
            value_str,
            config_def.config_type,
            config_def.config_id,
            'ro' if config_def.config_readonly else 'rw'
        ]

    def _set_property(self, config_id: str, value: Any) -> None:
        """Assign a configuration value as an attribute of the instance.

        Args:
            config_id (str): The configuration identifier.
            value (Any): The value to assign.
        """
        setattr(self, config_id, value)
