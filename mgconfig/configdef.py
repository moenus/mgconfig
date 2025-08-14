from typing import Callable, Optional, Any, Union
from dataclasses import dataclass
import yaml
from .config_types import ConfigTypes
from .extension_system import DefaultFunctions, DefaultValues
import keyword
from pathlib import Path

CONFIG_PREFIX = 'config_'


class ConfigDefs:
    def __init__(self, cfg_defs_filepaths: Union[str, list[str]]):
        self.config_defs = {}

        if isinstance(cfg_defs_filepaths, (str, Path)):
            cfg_defs_filepaths = [cfg_defs_filepaths]
        for path in map(Path, cfg_defs_filepaths):
            with path.open("r", encoding="utf-8") as f:
                cfg_def_data = yaml.safe_load(f)
            if not isinstance(cfg_def_data, list):
                raise ValueError(
                    f"Invalid config format in {path}, expected a list.")
            self._parse_config_defs_data(cfg_def_data, self.config_defs)

    def _parse_config_defs_data(self, config_defs_data: list, config_def_dict) -> list:
        for section in config_defs_data:
            for config_def in section.get('configs', []):
                def_dict = {}
                for field in ['section', 'prefix']:
                    self._read_data(field, section, def_dict,  mandatory=True)
                if def_dict['config_prefix'].startswith('_') or def_dict['config_prefix'] != def_dict['config_prefix'].lower():
                    raise ValueError(
                        f'{def_dict["config_prefix"]} is invalid section prefix.')
                for field in ['name', 'type']:
                    self._read_data(field, config_def,
                                    def_dict,  mandatory=True)
                def_dict['config_name'] = def_dict['config_name'].lower()
                def_dict['config_id'] = f"{def_dict['config_prefix']}_{def_dict['config_name']}"
                default_function = config_def.get('default_function')

                if default_function and callable(DefaultFunctions().get(default_function)):
                    # execute default function
                    def_dict['config_default'] = DefaultFunctions().get(
                        default_function)()
                else:
                    if def_dict['config_id'] in DefaultValues().dict.keys():
                        def_dict['config_default'] = DefaultValues().get(
                            def_dict['config_id'])
                    else:
                        self._read_data('default', config_def, def_dict)
                for field in ['env', 'description']:
                    self._read_data(field, config_def, def_dict)
                self._read_data('readonly', config_def,
                                def_dict, default=False)
                cfg_def = ConfigDef(**def_dict)
                if cfg_def.config_id not in config_def_dict:
                    config_def_dict[cfg_def.config_id] = cfg_def
                else:
                    raise ValueError(
                        f'Duplicate definition for {cfg_def.config_id} found.')

    def _read_data(self, name: str, source: dict, target: dict, default=None,  mandatory: bool = False) -> None:
        if mandatory and name not in source:
            raise ValueError(
                f'Configuration definition: mandatory field "{name}" missing.')
        else:
            target[CONFIG_PREFIX+name] = source.get(name, default)


@dataclass
class ConfigDef():
    config_id: str
    config_type: str
    config_readonly: bool
    config_name: str
    config_prefix: str
    config_section: str
    config_env: Optional[str] = None
    config_description: Optional[str] = None
    config_default: Any = None

    def __post_init__(self):
        # --- Identifier validation ---
        if not self.config_id.isidentifier() or keyword.iskeyword(self.config_id):
            raise ValueError(
                f"{self.config_id!r} is not a valid Python identifier.")

        # --- Config type validation ---
        if self.config_type not in ConfigTypes._config_types:
            raise ValueError(
                f"{self.config_id}: config type '{self.config_type}' is invalid.")

        # --- Default value type validation ---
        if self.config_default is not None:
            result, _ = ConfigTypes.parse_value(
                self.config_default, self.config_type)
            if not result:
                raise ValueError(
                    f"{self.config_id}: default value type does not match config type.")

        # --- Readonly field type safety ---
        if not isinstance(self.config_readonly, bool):
            raise ValueError(
                f"{self.config_id}: config_readonly must be a boolean.")

        # --- Mandatory string fields ---
        for field_name in ("config_id", "config_type", "config_name", "config_prefix", "config_section"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{self.config_id}: {field_name} must be a non-empty string.")
