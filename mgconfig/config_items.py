# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from typing import Any, Optional, Dict
from .config_defs import ConfigDef
from .config_types import ConfigTypes
from dataclasses import asdict


class ConfigItem():
    def __init__(self, cfg_def: ConfigDef, value: Optional[Any] = None, source: Optional[str] = None, new:bool = False) -> None:
        """
        Initialize a ConfigValue.

        Args:
            cfg_def (ConfigDef): Configuration definition object containing ID, type, and defaults.
            value_src (Any, optional): Initial raw value source (env, file, secret, etc.).
            source (str, optional): Description of the source (e.g., 'env', 'file', 'default').
        """
        # self._cfg_def = cfg_def
        self.value = value
        self.source = source
        self.new = new
        for k, v in asdict(cfg_def).items():
            if not hasattr(self, k):  # nur wenn Attribut existiert
                setattr(self, k, v)

    def __str__(self) -> str:
        """
        Return the current value formatted for display.

        Returns:
            str: Current value as string.
        """
        return ConfigTypes.display_value(self.value, self.config_type)

    @property
    def value_str(self):
        return str(self)

    @property
    def source_str(self):
        return str(self.source) if not self.new else 'new'

    @property
    def readonly_flag(self):
        return 'ro' if self.config_readonly else 'rw'

    def get_display_dict(self) -> Dict[str, str]:
        """Build a row representing a configuration value and metadata.

        Args:
            config_def (ConfigDef): The configuration definition object.
            value_str (str): The string representation of the value.
            source (str): The source of the value (e.g., "env", "file", "new").

        Returns:
            List[Any]: A row containing configuration metadata and value.
        """
        return {
            'config_id': self.config_id,
            'config_section': self.config_section,
            'config_prefix': self.config_prefix,
            'config_name': self.config_name,
            'config_type': self.config_type,
            'config_env': self.config_env or '',
            'config_default': self.config_default or '',
            'readonly_flag': self.readonly_flag,
            'source_str': self.source_str,
            'value_str': self.value_str,

        }


class ConfigItems(dict):

    """
    Acts as a collection (dict-like) of ConfigValue.

    """

    def set(self, key: str, item: ConfigItem):
        if not isinstance(item, ConfigItem):
            raise KeyError(f'Item for configuration key {key} invalid.')
        self[key] = item

    def get(self, key, fail_on_error=False) -> Optional[Any]:
        if key in self:
            return self[key]
        if fail_on_error:
            raise KeyError(
                f'Item for configuration key {key} not found.')

    def get_value(self, key, default=None, fail_on_error=False) -> Optional[Any]:
        item = self.get(key,fail_on_error)
        if item:
            return item.value
        else:
            return default    


config_items = ConfigItems()
config_items_new = ConfigItems()
