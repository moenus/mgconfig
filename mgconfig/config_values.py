# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from .config_defs import ConfigDef
from .config_types import ConfigTypes


class ConfigValue():
    def __init__(self, cfg_def: ConfigDef, value: Optional[Any] = None, source: Optional[str] = None) -> None:
        """
        Initialize a ConfigValue.

        Args:
            cfg_def (ConfigDef): Configuration definition object containing ID, type, and defaults.
            value_src (Any, optional): Initial raw value source (env, file, secret, etc.).
            source (str, optional): Description of the source (e.g., 'env', 'file', 'default').
        """
        self._cfg_def = cfg_def
        self._value = value
        self._source = source

    def __str__(self) -> str:
        """
        Return the current value formatted for display.

        Returns:
            str: Current value as string.
        """
        return ConfigTypes.display_value(self._value, self._cfg_def.config_type)

    @property
    def value(self):
        return self._value

    @property
    def source(self):
        return self._source

    @property
    def config_id(self):
        return self._cfg_def.config_id

    @property
    def config_type(self):
        return str(self._cfg_def.config_type)

    @property
    def cfg_def(self):
        return self._cfg_def

class ConfigValues(dict):

    """
    ConfigValues

    Acts as a collection (dict-like) of ConfigValue.

    """

    def set(self, key: str, value_obj: ConfigValue):
        if not isinstance(value_obj, ConfigValue):
            raise KeyError(f'Value for key {key} invalid.')
        self[key] = value_obj

    def get(self, key, default=None, fail_on_error=False) -> Optional[Any]:
        if fail_on_error and key not in self:
            raise KeyError(
                f'Value for configuration item key {key} not found.')
        if key in self:
            return self[key]
        return default


config_values = ConfigValues()
config_values_new = ConfigValues()

# cfg_def = 'abc'

# item1 = ConfigValue2(cfg_def, 123, 'mond')
# item2 = ConfigValue2(cfg_def, 456, 'sonne')
# config_values.set('abc', item1)
# config_values.set('def', item2)

# print(config_values.get('abc').value)
# print(len(config_values))
# config_values.clear()
# print(len(config_values))
