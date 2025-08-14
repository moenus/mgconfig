from .config_types import ConfigTypes
from typing import Any, Optional


class ConfigValue():
    """
    Represents a configuration value with type enforcement and display/output utilities.
    """
    def __init__(self, cfg_def: Any, value_src: Optional[Any] = None, source: Optional[str] = None) -> None:
        """
        Initialize ConfigValue with a config definition, optional source value, and source info.
        """
        self._cfg_def = cfg_def
        self.initialize_value(value_src, source)

    def __str__(self) -> str:
        return self.display_current()

    def display_current(self) -> str:
        return ConfigTypes.display_value(self._value, self._cfg_def.config_type)

    def display_new(self) -> str:
        return ConfigTypes.display_value(self._value_new, self._cfg_def.config_type)

    def display_default(self) -> str:
        return ConfigTypes.display_value(self._cfg_def.config_default, self._cfg_def.config_type)

    def output_current(self) -> Any:
        return ConfigTypes.output_value(self._value, self._cfg_def.config_type)

    def output_new(self) -> Any:
        return ConfigTypes.output_value(self._value_new, self._cfg_def.config_type)

    def _parse_value_src(self) -> None:
        result, self._value = ConfigTypes.parse_value(
            self.value_src, self._cfg_def.config_type)
        if not result:
            raise ValueError(
                f'Config {self._cfg_def.config_id}: value is not of config type {self._cfg_def.config_type}.')

    def initialize_value(self, value_src: Any, source: str):
        self.source = source
        self.value_src = value_src
        self._value_new = None
        self._value = None
        self._parse_value_src()

    @property
    def value(self):
        return self._value

    @property
    def value_new(self):
        return self._value_new
        
    @value_new.setter
    def value_new(self, new_value: Any):
        test_value = ConfigTypes.output_value(
            new_value, self._cfg_def.config_type)
        result, parsed_value = ConfigTypes.parse_value(
            test_value, self._cfg_def.config_type)
        if not result or new_value != parsed_value:
            raise ValueError(
                f'Config {self._cfg_def.config_id}: value is not of config type {self._cfg_def.config_type}.')
        self._value_new = new_value

    def apply_change_immediately(self) -> None:
        self._value = self._value_new
