# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from .configdef import ConfigDefs, ConfigDef

from .config_value import ConfigValue
from .value_store import ValueStoreFile, ValueStoreSecure, ValueStoreEnv, ValueStoreDefault, ConfigValueSource, ValueStores
from .extension_system import PostProcessing
from typing import Any, Dict, List, Optional, Tuple, Type, Union
import re
from types import SimpleNamespace
from .helpers import logger


class Configuration():
    """ this class reperesents the configuration values which are defined in  
        environment variables and a json configuration file. 
        If a value is not found in these sources a default value from cfg_defs is used.

    """

    # def __new__(cls,cfg_defs_filepaths: Union[str, List[str]]):
    #     # Name-mangled, so private to each class - singleton pattern
    #     private_instance_name = f"_{cls.__name__}__instance"

    #     if not hasattr(cls, private_instance_name):
    #         instance = super().__new__(cls, cfg_defs_filepaths)
    #         setattr(cls, private_instance_name, instance)
    #     return getattr(cls, private_instance_name)

    def __init__(self, cfg_defs_filepaths: Union[str, List[str]]):
        self._config_values = {}
        self.extended = SimpleNamespace()
        self._cfg_def_dict = ConfigDefs(cfg_defs_filepaths).config_defs
        self._configuration_values_initialization()

    def _configuration_values_initialization(self):
        # loop through the all config defs and get config values
        for cfg_def in self._cfg_def_dict.values():
            self._set_config_value(
                cfg_def.config_id, self._create_value_object(cfg_def))

        # call provided post processing functions
        for pp_func in PostProcessing().dict.values():
            pp_func(self)

    def _create_value_object(self, cfg_def: ConfigDef) -> ConfigValue:
        """
        Retrieve and construct a ConfigValue object for a given definition.

        Retrieval order:
          1. Secure store (for secrets) or environment variables
          2. Configuration file (if not read-only)
          3. Default values from definitions
        """
        value_src, source = (None, None)
        if cfg_def.config_type == 'secret':
            value_src, source = self._retrieve_value(
                ValueStoreSecure, cfg_def.config_id)
        else:
            value_src, source = self._retrieve_value(
                ValueStoreEnv, cfg_def.config_id)
            if value_src is None and not cfg_def.config_readonly:
                value_src, source = self._retrieve_value(
                    ValueStoreFile, cfg_def.config_id)
            if value_src is None:
                value_src, source = self._retrieve_value(
                    ValueStoreDefault, cfg_def.config_id)
            # expand $ variables in string values:
            if (type(value_src) == str) and ('$' in value_src):
                value_src = self._replace_var(value_src, self._config_values)

        config_value = ConfigValue(cfg_def, value_src, source)
        return config_value

    def _retrieve_value(self, value_store_class: Type, config_id: str) -> Tuple[Any, Optional[str]]:
        """
        Retrieve a value from a specific value store, initializing the value store from self if needed.
        """
        value_store = ValueStores.get(value_store_class, init_config=self)
        return value_store.retrieve_value(config_id) if value_store else (None, None)

    def _save_value(self, value_store_class: Type, config_id: str, value: Any) -> Tuple[Any, Optional[str]]:
        """
        Save a value to a specific value store.
        """
        value_store = ValueStores.get(value_store_class)
        return value_store.save_value(config_id, value) if value_store else (None, None)

    def _replace_var(self, value_src: str, config_values: dict) -> str:
        """
        Replace $(varname) placeholders in the given string with corresponding values
        from config_values. Unmatched placeholders are left unchanged.

        Parameters
        ----------
        value_src : str
            The original string with potential $(varname) placeholders.
        config_values : dict[str, ConfigValue]
            Mapping of configuration IDs to their ConfigValue objects.

        Returns
        -------
        str
            String with placeholders replaced.
        """
        pattern = re.compile(r"\$\(([^)]+)\)")

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            if var_name in config_values:
                return str(config_values[var_name].value_src)
            return match.group(0)  # Leave as-is if not found

        return pattern.sub(replacer, value_src)

    def _set_config_value(self, config_id, config_value):
        self._config_values[config_id] = config_value
        setattr(self, config_id, config_value.value)

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
        if config_id not in self._config_values:
            return False
        cfg_def = self._cfg_def_dict[config_id]
        if cfg_def.config_readonly:
            raise ValueError(
                f'Readonly configuration {config_id} cannot be overwritten.')
        config_value = self._config_values[config_id]
        config_value.value_new = new_value
        output = config_value.output_new()
        if cfg_def.config_type == 'secret':
            self._save_value(ValueStoreSecure, config_id, output)
            source = ConfigValueSource.SECRET
            logger.info(f'Secret value for {config_id} was changed.')
        else:
            self._save_value(ValueStoreFile, config_id, output)
            source = ConfigValueSource.CFGFILE
            logger.info(
                f'Value for {config_id} was changed from [{config_value.value}] to [{new_value}]')
        if apply_immediately == True:
            config_value.initialize_value(output, source)
            setattr(self, config_id, config_value.value)
        return True

    def get_new_masterkey(self) -> str:
        """
        Prepare a new master key from the secure value store.
        This method interacts with the secure value store to generate 
        and return a fresh master key.

        Returns:
            str: A newly generated master key.
        """
        return ValueStores.get(ValueStoreSecure).prepare_new_masterkey()

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
