# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from .config_types import ConfigTypes
from .config_defs import ConfigDefs, ConfigDef
from typing import Any, Optional
from .value_stores import ValueStoreFile, ValueStoreSecure, ValueStoreEnv, ValueStoreDefault, ConfigValueSource
import re
from .helpers import config_logger
from .config_items import config_items, ConfigItem, config_items_new


class ConfigItemHandler:

    @classmethod
    def build(cls):
        for cfg_def in ConfigDefs().values():
            cls._add_value_object(cfg_def)

    @classmethod
    def _add_value_object(cls, cfg_def: ConfigDef) -> ConfigItem:
        """
        Retrieve and construct a ConfigValue object for a given definition.

        Retrieval order:
          1. Secure store (for secrets) or environment variables
          2. Configuration file (if not read-only)
          3. Default values from definitions
        """
        value_src, source = (None, None)
        if cfg_def.config_type == 'secret':
            value_src, source = ValueStoreSecure().retrieve_value(
                cfg_def.config_id)
        else:
            value_src, source = ValueStoreEnv().retrieve_value(cfg_def.config_id)
            if value_src is None and not cfg_def.config_readonly:
                value_src, source = ValueStoreFile().retrieve_value(cfg_def.config_id)
            if value_src is None:
                value_src, source = ValueStoreDefault().retrieve_value(cfg_def.config_id)
            # expand $ variables in string values:
            if isinstance(value_src, str) and ('$' in value_src):
                value_src = ConfigItemHandler._replace_var(value_src)

        result, parsed_value = ConfigTypes.parse_value(
            value_src, cfg_def.config_type)
        config_logger.debug(
            f'Configuration [{cfg_def.config_id}]: value: {value_src} --[{cfg_def.config_type}]--> {parsed_value}')
        if not result:
            raise ValueError(
                f'Config id {cfg_def.config_id}: Value {value_src} is not of config type {cfg_def.config_type}.')
        config_items.set(cfg_def.config_id, ConfigItem(
            cfg_def, parsed_value, source))

    @staticmethod
    def _replace_var(value_src: str, visited: set[str] | None = None) -> str:
        """
        Replace $(varname) placeholders in the given string with corresponding values
        from config_values. Unmatched placeholders are left unchanged.

        Parameters
        ----------
        value_src : str
            The original string with potential $(varname) placeholders.

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
                raise ValueError(
                    f"Circular reference detected for variable '{var_name}'")

            if var_name in config_items:
                visited.add(var_name)
                try:
                    var_text = ConfigItemHandler._insertstr(var_name)
                    if var_text is not None:
                        return ConfigItemHandler._replace_var(str(var_text), visited)
                    else:
                        return match.group(0)  # leave as-is if None
                finally:
                    visited.remove(var_name)

            return match.group(0)  # leave as-is if not found

        return pattern.sub(replacer, value_src)

    @staticmethod
    def _insertstr(var_name):
        config_value = config_items.get(var_name)
        if config_value is not None:
            cfg_def = ConfigDefs().get(var_name)
            return ConfigTypes.output_value(config_value.value, cfg_def.config_type)

    @staticmethod
    def save_new_value(config_id, new_value: Any, apply_immediately: bool = False) -> bool:
        """
        Save a new configuration value to the appropriate store.
        Optionally apply it immediately in the current instance.
        """
        cfg_def = ConfigDefs().get(config_id)
        if cfg_def.config_readonly:
            raise ValueError(
                f'Readonly configuration {config_id} cannot be overwritten.')
        output = ConfigTypes.output_value(new_value, cfg_def.config_type)
        if cfg_def.config_type == 'secret':
            ValueStoreSecure().save_value(
                cfg_def.config_id, output)
            source = ConfigValueSource.ENCRYPT
            config_logger.info(
                f'Secret value for id {config_id} was changed.')
        else:
            ValueStoreFile().save_value(
                config_id, output)
            source = ConfigValueSource.CFGFILE
            config_logger.info(
                f'Configuration [{config_id}]: value was changed from [{config_items.get(config_id)}] to [{new_value}]')
        if apply_immediately:
            config_items.set(config_id, ConfigItem(
                cfg_def, new_value, source))
            if config_id in config_items_new:
                del config_items_new[config_id]
        else:
            config_items_new.set(
                config_id, ConfigItem(cfg_def, new_value, source, new=True))

        return True

    @staticmethod
    def reset_values():
        config_items.clear()
        config_items_new.clear()
