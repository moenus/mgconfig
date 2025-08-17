# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT
import base64
from datetime import datetime, time, date
from pathlib import Path
from typing import Callable, Optional, Any

PARSE_FUNC = 'parse_fn'
DISPLAY_FUNC = 'disp_fn'
OUTPUT_FUNC = 'out_fn'
VALUE_CLASS = 'class'


class ConfigTypes():
    _config_types = {}

    @staticmethod
    def add_type(name: str,
                 value_class: Any,
                 parse_func: Callable[[Any, str], Any],
                 display_func: Optional[Callable[[Any, str], Any]] = None,
                 output_func: Optional[Callable[[Any, str], Any]] = None) -> None:
        """
        Register a configuration type with its parsing and optional display/output functions.

        Parameters
        ----------
        name : str
            The identifier for the configuration type.
        parse_func : Callable[[Any, str], Any]
            Function to parse the raw configuration value.
        display_func : Optional[Callable[[Any, str], Any]], optional
            Function to convert the value for display (default is None).
        output_func : Optional[Callable[[Any, str], Any]], optional
            Function to convert the value for output (default is None).
        """
        if value_class and not isinstance(value_class, type):
            raise ValueError(
                f'Config Type {name}: {value_class} is not a valid class/type.')
        ConfigTypes._config_types[name] = {
            VALUE_CLASS: value_class,
            PARSE_FUNC: parse_func,
            DISPLAY_FUNC: display_func,
            OUTPUT_FUNC: output_func,
        }

    @staticmethod
    def get_function(val_type: str, func_type: str):
        if val_type not in ConfigTypes._config_types:
            raise ValueError(f"Unsupported value type: {val_type}")
        return ConfigTypes._config_types[val_type][func_type]

    @staticmethod
    def display_value(value: Any, val_type: str) -> str:
        display_function = ConfigTypes.get_function(
            val_type, DISPLAY_FUNC)
        if display_function is not None and value is not None:
            return display_function(value)
        return str(value)

    @staticmethod
    def parse_value(value: Any, val_type: str) -> tuple[bool, Any]:
        parse_function = ConfigTypes.get_function(val_type, PARSE_FUNC)
        if parse_function is None or value is None:
            return True, value
        else:
            try:
                parsed_value = parse_function(value)
                if parsed_value is not None:
                    return True, parsed_value
            except:
                pass
        return False, None

    @staticmethod
    def output_value(value: Any, val_type: str) -> Any:
        if value is None:
            return None
        value_class = ConfigTypes._config_types[val_type][VALUE_CLASS]
        if value_class and not isinstance(value, value_class):
            raise ValueError(
                f'Type of value is not compatible with configuration type {val_type}')
        output_function = ConfigTypes.get_function(
            val_type, OUTPUT_FUNC)
        if output_function is not None and value is not None:
            return output_function(value)
        return value

    @staticmethod
    def _parse_int_positive(value: Any) -> int:
        assert int(value) >= 0
        return int(value)

    @staticmethod
    def _parse_base64(value: Any) -> str:
        return base64.b64decode(value)

    @staticmethod
    def _parse_date(value: Any) -> datetime.date:
        return datetime.fromisoformat(value).date()

    @staticmethod
    def _display_date(value: date) -> str:
        return value.isoformat()

    @staticmethod
    def _parse_time(value: Any) -> datetime.time:
        if value.count(":") == 1:
            return datetime.strptime(value, "%H:%M").time()
        else:
            return datetime.strptime(value, "%H:%M:%S").time()

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        if type(value) == bool:
            return value

    @staticmethod
    def _output_path(value: Path) -> str:
        return value.as_posix()

    @staticmethod
    def _output_base64(value: Path) -> str:
        return base64.b64encode(value).decode("utf-8")

    @staticmethod
    def _display_asterix(value: Path) -> str:
        return '*****'

    @staticmethod
    def list_all() -> list:
        return [key for key in ConfigTypes._config_types.keys()]


# ------------------------------------------------------
# add the basic types
#-------------------------------------------------------
ConfigTypes.add_type('str', str, str, None, None)
ConfigTypes.add_type('int', int, int, str, None)
ConfigTypes.add_type('float', float, float, str, None)
ConfigTypes.add_type('bool', bool, ConfigTypes._parse_bool, str, None)
ConfigTypes.add_type(
    'date', date, ConfigTypes._parse_date, ConfigTypes._display_date, str)
ConfigTypes.add_type(
    'time', time, ConfigTypes._parse_time, str, str)
ConfigTypes.add_type(
    'path', Path, Path, str, ConfigTypes._output_path)
ConfigTypes.add_type(
    'secret', str, str, ConfigTypes._display_asterix, None)
ConfigTypes.add_type('bytes', bytes, ConfigTypes._parse_base64,
                     ConfigTypes._display_asterix, ConfigTypes._output_base64)
ConfigTypes.add_type('hidden', None, None,
                     ConfigTypes._display_asterix, None)
