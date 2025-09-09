# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from typing import Any, Optional, Dict
from .config_defs import ConfigDef
from .config_types import ConfigTypes
from dataclasses import asdict


class ConfigItem():
    """Represents a configuration entry with metadata and a value."""

    def __init__(self, cfg_def: ConfigDef, value: Optional[Any] = None, source: Optional[str] = None, new: bool = False) -> None:
        """Initialize a ConfigItem.

        Args:
            cfg_def (ConfigDef): Configuration definition containing ID, type, defaults, etc.
            value (Any, optional): Initial value for this configuration item. Defaults to None.
            source (str, optional): Description of the value source (e.g., "env", "file", "default"). Defaults to None.
            new (bool, optional): Whether the value is newly added. Defaults to False.
        """
        # self._cfg_def = cfg_def
        self.value = value
        self.source = source
        self.new = new
        for k, v in asdict(cfg_def).items():
            if not hasattr(self, k):  # nur wenn Attribut existiert
                setattr(self, k, v)

    def __str__(self) -> str:
        """Return the current value formatted for display.

        Returns:
            str: Display representation of the current value.
        """
        return ConfigTypes.display_value(self.value, self.config_type)

    @property
    def value_str(self) -> str:
        """String representation of the current value.

        Returns:
            str: Value as string.
        """
        return str(self)

    @property
    def source_str(self) -> str:
        """String representation of the value source.

        Returns:
            str: Source name (e.g., "env", "file", "default") or "new" if marked as new.
        """
        return str(self.source) if not self.new else 'new'

    @property
    def readonly_flag(self) -> str:
        """Read-only indicator for the configuration item.

        Returns:
            str: "ro" if the config is read-only, otherwise "rw".
        """
        return 'ro' if self.config_readonly else 'rw'

    def get_display_dict(self) -> Dict[str, str]:
        """Build a dict representing the configuration metadata and value.

        Returns:
            Dict[str, str]: Dictionary with configuration metadata (ID, name, section, etc.),
            source, flags, and value string.
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
    """Collection of configuration items (dict-like)."""

    def set(self, key: str, item: ConfigItem) -> None:
        """Set a configuration item.

        Args:
            key (str): Configuration key.
            item (ConfigItem): Configuration item to store.

        Raises:
            TypeError: If the provided item is not a ConfigItem.
        """
        if not isinstance(item, ConfigItem):
            raise TypeError(f'Item for configuration key {key} invalid.')
        self[key] = item

    def get(self, key: str, fail_on_error: bool = False) -> Optional[ConfigItem]:
        """Retrieve a configuration item.

        Args:
            key (str): Configuration key.
            fail_on_error (bool, optional): If True, raise an error when key is not found.
                Defaults to False.

        Returns:
            Optional[ConfigItem]: The configuration item if found, otherwise None.

        Raises:
            KeyError: If the key is not found and fail_on_error is True.
        """
        if key in self:
            return self[key]
        if fail_on_error:
            raise KeyError(
                f'Item for configuration key {key} not found.')

    def get_value(self, key: str, default: Any = None, fail_on_error: bool = False) -> Any:
        """Retrieve the value of a configuration item.

        Args:
            key (str): Configuration key.
            default (Any, optional): Default value if key is not found. Defaults to None.
            fail_on_error (bool, optional): If True, raise an error when key is not found.
                Defaults to False.

        Returns:
            Any: The configuration value if found, otherwise the default.

        Raises:
            KeyError: If the key is not found and fail_on_error is True.
        """
        item = self.get(key, fail_on_error)
        if item:
            return item.value
        else:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Export only configuration values without metadata.

        Returns:
            Dict[str, Any]: Mapping of configuration key → value.
        """
        return {key: item.value for key, item in self.items()}     


config_items = ConfigItems()
config_items_new = ConfigItems()
