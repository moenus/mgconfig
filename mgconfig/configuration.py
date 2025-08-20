# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from .config_defs import ConfigDefs, ConfigDef
from .config_values import ConfigValue, ConfigValues
from .extension_system import PostProcessing
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from types import SimpleNamespace
from .helpers import logger


class Configuration():
    """ this class reperesents the configuration values which are defined in  
        environment variables and a json configuration file. 
        If a value is not found in these sources a default value from cfg_defs is used.

    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cfg_defs_filepaths: Union[str, List[str]] = None):
        if not hasattr(self, "_initialized"):  # avoid re-initializing
            if cfg_defs_filepaths is None:
                raise TypeError(f'Config definition filepath is missing.')
            self._initialized = True
            self.extended = SimpleNamespace()
            self._cfg_def_dict = ConfigDefs(cfg_defs_filepaths)
            self._config_values = ConfigValues(self._cfg_def_dict)

            for config_id in self._config_values:
                setattr(self, config_id, self._config_values[config_id].value)

            # call provided post processing functions
            for pp_func in PostProcessing().dict.values():
                pp_func(self)

    def get(self, config_id: str, fail_on_error: bool = False) -> Any:
        """
        Get the current value for a configuration ID.
        """
        if config_id in self.__dict__:
            return self.__dict__[config_id]
        if fail_on_error:
            raise ValueError(f'Configuration value {config_id} not found.')

    def get_config_value(self, config_id: str, fail_on_error: bool = True) -> ConfigValue:
        """
        Get the ConfigValue object for a configuration ID.
        """
        if config_id in self._config_values:
            return self._config_values[config_id]
        if fail_on_error:
            raise ValueError(f'Configuration value {config_id} not found.')

    def get_cfg_def(self, config_id: str, fail_on_error: bool = True) -> Optional[ConfigDef]:
        """
        Get the configuration definition for a configuration ID.
        """
        if config_id in self._cfg_def_dict:
            return self._cfg_def_dict[config_id]
        if fail_on_error:
            raise ValueError(
                f'Configuration definition {config_id} not found.')

    @property
    def data_rows(self) -> List[List[Any]]:
        """
        Return all configuration values and their metadata as rows for table display.
        Includes both current and pending (new) values.
        """
        def get_cfg_def_row(config_def, config_value, new_value_mode=False, new_value_source='new'):
            return [config_def.config_section,
                    config_def.config_name,
                    config_def.config_env if config_def.config_env is not None else '',
                    config_def.config_default if config_def.config_default is not None else '',
                    config_value.source if not new_value_mode else new_value_source,
                    config_value.display_current() if not new_value_mode else
                    config_value.display_new(),
                    config_def.config_type,
                    config_def.config_id,
                    'ro' if config_def.config_readonly else 'rw']
        data_table = []
        for cfg_def in self._cfg_def_dict.values():
            config_value = self._config_values[cfg_def.config_id]
            data_table.append(get_cfg_def_row(cfg_def, config_value))
            if config_value.value_new is not None:
                data_table.append(get_cfg_def_row(cfg_def, config_value,
                                                  new_value_mode=True))
        return data_table

    def save_new_value(self, config_id: str, new_value: Any, apply_immediately: bool = False) -> bool:
        """
        Save a new configuration value to the appropriate store.
        Optionally apply it immediately in the current instance.
        """
        self._config_values.save_new_value(
            config_id, new_value, apply_immediately)
        if apply_immediately:
            setattr(self, config_id, self._config_values[config_id].value)
        return



    def set_extended_item(self, name: str, value: Any):
        """
        Set or add an attribute to the extended object.

        Args:
            name (str): The name of the attribute to set.
            value (Any): The value to assign to the attribute.
        """
        setattr(self.extended, name, value)

    def extended_item_exists(self, name: str) -> bool:
        """
        Check if an attribute exists in the extended object.

        Args:
            name (str): The name of the attribute to check.

        Returns:
            bool: True if the attribute exists, False otherwise.
        """
        return hasattr(self.extended, name)

    def get_extended_item(self, name: str) -> Any:
        """
        Retrieve the value of an attribute from the extended object.

        Args:
            name (str): The name of the attribute to retrieve.

        Returns:
            Any: The value of the attribute if it exists, otherwise None.
        """
        return self.extended.__dict__.get(name)

    @classmethod
    def reset(cls):
        """Delete the current singleton instance."""
        cls._instance = None    
