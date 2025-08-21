# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from .config_types import ConfigTypes
from .config_defs import ConfigDefs, ConfigDef
from typing import Any, Optional
from .value_stores import ValueStoreFile, ValueStoreSecure, ValueStoreEnv, ValueStoreDefault, ConfigValueSource, ValueStores
import re
from .helpers import logger




class ConfigValue():
    """
    Represents a configuration value with type enforcement and
    conversion utilities for display, output, and persistence.
    """    
    """
    ConfigValue

    Represents a single configuration value.

    Handles type parsing, validation, conversion for display/output.

    Provides methods to get current, new, and default values in both display and output forms.

    Uses ConfigTypes for type handling and ConfigDef for metadata.

    value_new setter ensures type validation before assigning.

    initialize_value resets and parses the value.
    """
    """
    Represents a configuration value with type enforcement and display/output utilities.
    """

    def __init__(self, cfg_def: ConfigDef, value_src: Optional[Any] = None, source: Optional[str] = None) -> None:
        """
        Initialize a ConfigValue.

        Args:
            cfg_def (ConfigDef): Configuration definition object containing ID, type, and defaults.
            value_src (Any, optional): Initial raw value source (env, file, secret, etc.).
            source (str, optional): Description of the source (e.g., 'env', 'file', 'default').
        """
        self._cfg_def = cfg_def
        self.initialize_value(value_src, source)

    def __str__(self) -> str:
        return self.display_current()

    def display_current(self) -> str:
        """
        Return the current value formatted for display.

        Returns:
            str: Current value as string.
        """        
        return ConfigTypes.display_value(self._value, self.config_type)

    def display_new(self) -> str:
        """
        Return the staged new value formatted for display.

        Returns:
            str: New value as string, or None if not set.
        """        
        return ConfigTypes.display_value(self._value_new, self.config_type)

    def display_default(self) -> str:
        """
        Return the default value formatted for display.

        Returns:
            str: Default value as string.
        """        
        return ConfigTypes.display_value(self.config_default, self.config_type)

    def output_current(self) -> Any:
        """
        Return the current value formatted for persistence/output.

        Returns:
            Any: Current parsed and type-converted value.
        """        
        return ConfigTypes.output_value(self._value, self.config_type)

    def output_new(self) -> Any:
        """
        Return the staged new value formatted for persistence/output.

        Returns:
            Any: New parsed and type-converted value.
        """        
        return ConfigTypes.output_value(self._value_new, self.config_type)

    def _parse_value_src(self) -> None:
        self._value = self._validate_and_parse(self.value_src)


    def _validate_and_parse(self, value: Any) -> None:
        """
        Validate and parse a raw value against the config type.

        Args:
            value (Any): Raw input value.

        Returns:
            Any: Parsed value in the correct type.

        Raises:
            ValueError: If the value does not match the expected type.
        """        
        result, parsed_value = ConfigTypes.parse_value(
            value, self.config_type)
        if not result:
            raise ValueError(
                f'Config {self.config_id}: value is not of config type {self.config_type}.')
        return parsed_value    


    def initialize_value(self, value_src: Any, source: str):
        """
        Initialize or reset the value.

        Args:
            value_src (Any): Raw source value.
            source (str): Source identifier.
        """        
        self.source = source
        self.value_src = value_src
        self._value_new = None
        self._value = None
        self._parse_value_src()

    @property
    def value(self):
        """Any: The current parsed value."""        
        return self._value

    @property
    def value_new(self):
        """Any: The staged new value."""        
        return self._value_new

    @value_new.setter
    def value_new(self, new_value: Any):
        """
        Stage a new value with type validation.

        Args:
            new_value (Any): New raw value to set.

        Raises:
            ValueError: If the new value is invalid.
        """        
        test_value = ConfigTypes.output_value(
            new_value, self.config_type)
        parsed_value = self._validate_and_parse(test_value)
        if new_value == parsed_value:
            self._value_new = parsed_value


    @property
    def config_id(self):
        """str: The unique configuration identifier."""        
        return self._cfg_def.config_id

    @property
    def config_type(self):
        """str: The type of the configuration (e.g., string, int, secret)."""        
        return self._cfg_def.config_type

    @property
    def config_default(self):
        """Any: The default configuration value."""        
        return self._cfg_def.config_default


class ConfigValues:

    """
    ConfigValues

    Acts as a collection (dict-like) of ConfigValue.

    Supports full dict-like behavior (__getitem__, __len__, __contains__, etc.).

    _add_value_object resolves config value sources in priority order:
    secret → env → file → default.

    _replace_var expands $(varname) placeholders with config values recursively.

    save_new_value persists new values to the correct ValueStore.
    """
    
    def __init__(self, cfg_defs: ConfigDefs):
        self._cfg_vals:dict[str, ConfigValue] = {}
        init_dict = {}
        for cfg_def in cfg_defs.values():
            self._add_value_object(cfg_def, cfg_defs, init_dict)

    def __getitem__(self, key):
        return self._cfg_vals[key]

    def __setitem__(self, key, value):
        self._cfg_vals[key] = value

    def __delitem__(self, key):
        del self._cfg_vals[key]

    def __contains__(self, key):
        return key in self._cfg_vals

    def keys(self):
        return self._cfg_vals.keys()

    def values(self):
        return self._cfg_vals.values()

    def items(self):
        return self._cfg_vals.items()

    def __iter__(self):
        return iter(self._cfg_vals)

    def __len__(self):
        return len(self._cfg_vals)

    def get(self, key, default=None):
        if key in self._cfg_vals:
            return self._cfg_vals[key]
        return default

    def _add_value_object(self, cfg_def: ConfigDef, cfg_defs: ConfigDefs, init_dict: dict[str, Any]) -> ConfigValue:
        """
        Retrieve and construct a ConfigValue object for a given definition.

        Retrieval order:
          1. Secure store (for secrets) or environment variables
          2. Configuration file (if not read-only)
          3. Default values from definitions
        """
        value_src, source = (None, None)
        if cfg_def.config_type == 'secret':
            value_src, source = ValueStores.retrieve_val(
                ValueStoreSecure, cfg_def.config_id, cfg_defs, init_dict)
        else:
            value_src, source = ValueStores.retrieve_val(
                ValueStoreEnv, cfg_def.config_id, cfg_defs, init_dict)
            if value_src is None and not cfg_def.config_readonly:
                value_src, source = ValueStores.retrieve_val(
                    ValueStoreFile, cfg_def.config_id, cfg_defs,  init_dict)
            if value_src is None:
                value_src, source = ValueStores.retrieve_val(
                    ValueStoreDefault, cfg_def.config_id, cfg_defs, init_dict)
            # expand $ variables in string values:
            if isinstance(value_src, str) and ('$' in value_src):
                value_src = self._replace_var(value_src, self._cfg_vals)

        self._cfg_vals[cfg_def.config_id] = ConfigValue(
            cfg_def, value_src, source)
        init_dict[cfg_def.config_id] = value_src

    def _replace_var(self, value_src: str, config_values: dict, visited: set[str] | None = None) -> str:
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
        if visited is None:
            visited = set()
        
        pattern = re.compile(r"\$\(([^)]+)\)")

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            if var_name in visited:
                raise ValueError(f"Circular reference detected for variable '{var_name}'")
            
            if var_name in config_values:
                visited.add(var_name)
                raw_value= config_values[var_name].value_src
                if isinstance(raw_value, str):
                    return self._replace_var(raw_value, config_values, visited.copy())
                return str(raw_value)
                    
            return match.group(0)  # Leave as-is if not found

        return pattern.sub(replacer, value_src)

    def save_new_value(self, config_id: str, new_value: Any, apply_immediately: bool = False) -> bool:
        """
        Save a new configuration value to the appropriate store.
        Optionally apply it immediately in the current instance.
        """
        if config_id not in self._cfg_vals:
            raise KeyError(
                f'Configuration ID {config_id} not found.')
        config_value = self._cfg_vals[config_id]
        cfg_def = config_value._cfg_def
        if cfg_def.config_readonly:
            raise ValueError(
                f'Readonly configuration {config_id} cannot be overwritten.')

        config_value.value_new = new_value
        output = config_value.output_new()
        
        if cfg_def.config_type == 'secret':
            ValueStores.save_val(ValueStoreSecure, config_id, output)
            source = ConfigValueSource.ENCRYPT
            logger.info(f'Secret value for {config_id} was changed.')
        else:
            ValueStores.save_val(ValueStoreFile, config_id, output)
            source = ConfigValueSource.CFGFILE
            logger.info(
                f'Value for {config_id} was changed from [{config_value.value}] to [{new_value}]')
        if apply_immediately:
            config_value.initialize_value(output, source)
