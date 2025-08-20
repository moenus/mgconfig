# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from typing import Callable, Optional, Any, Union
from dataclasses import dataclass
import yaml
from .config_types import ConfigTypes
from .extension_system import DefaultFunctions, DefaultValues
import keyword
from pathlib import Path
from enum import Enum

CONFIG_PREFIX = 'config'

class CDF(Enum):  # ConfigDef fields
    SECTION = 'section'
    PREFIX = 'prefix'
    NAME = 'name'
    ID = 'id'
    TYPE= 'type'
    READONLY = 'readonly'
    ENV= 'env'
    DEFAULT = 'default'
    DESCRIPTION = 'description'
    DEFAULT_FUNCTION = 'default_function'

    def __str__(self):
        # Return the stored value instead of "CDF.SECTION"
        return f'{CONFIG_PREFIX}_{self.value}'

    @property
    def src_name(self):
        return self.value        


class DefDict:
    def __init__(self):
        self.dict = {}

    def get(self, cdf) -> str:
        if not isinstance(cdf, CDF):
            raise KeyError(f'{cdf} is not instance of CDF.')
        if str(cdf) not in self.dict:
            raise KeyError(f'{str(cdf)} not found.')            
        return self.dict.get(str(cdf))     

    def set(self, cdf, value: str):
        if not isinstance(cdf, CDF):
            raise KeyError(f'{cdf} is not instance of CDF.')
        self.dict[str(cdf)] = value     
    

class ConfigDefs:
    def __init__(self, cfg_defs_filepaths: Union[str, list[str]]):
        self.cfg_defs = {}

        if isinstance(cfg_defs_filepaths, (str, Path)):
            cfg_defs_filepaths = [cfg_defs_filepaths]
        for path in map(Path, cfg_defs_filepaths):
            with path.open("r", encoding="utf-8") as f:
                cfg_def_data = yaml.safe_load(f)
            if not isinstance(cfg_def_data, list):
                raise ValueError(
                    f"Invalid config format in {path}, expected a list.")
            self._parse_config_defs_data(cfg_def_data, self.cfg_defs)

    def _parse_config_defs_data(self, config_defs_data: list, config_def_dict) -> list:
        for section in config_defs_data:
            for config_def in section.get('configs', []):
                def_dict = DefDict()
                for field in [CDF.SECTION, CDF.PREFIX]:
                    self._read_data(field, section, def_dict,  mandatory=True)
                if def_dict.get(CDF.PREFIX).startswith('_') or def_dict.get(CDF.PREFIX) != def_dict.get(CDF.PREFIX).lower():
                    raise ValueError(
                        f'{def_dict.get(CDF.PREFIX)} is invalid section prefix.')
                    
                for field in [CDF.NAME, CDF.TYPE]:
                    self._read_data(field, config_def,
                                    def_dict,  mandatory=True)
                def_dict.set(CDF.NAME, def_dict.get(CDF.NAME).lower())
                def_dict.set(CDF.ID, f"{def_dict.get(CDF.PREFIX)}_{def_dict.get(CDF.NAME)}")
                             
                default_function_name = config_def.get(CDF.DEFAULT_FUNCTION.src_name)
                if default_function_name and DefaultFunctions().contains(default_function_name):
                    default_function = DefaultFunctions().get(default_function_name)
                    if callable(default_function):
                        # execute default function
                        def_dict.set(CDF.DEFAULT, default_function())
                    else:
                        raise ValueError(f'{default_function} is not callable.')    
                else:
                    if def_dict.get(CDF.ID) in DefaultValues().dict.keys():
                        def_dict.set(CDF.DEFAULT, DefaultValues().get(def_dict.get(CDF.ID)))
                    else:
                        self._read_data(CDF.DEFAULT, config_def, def_dict)
                for field in [CDF.ENV, CDF.DESCRIPTION]:
                    self._read_data(field, config_def, def_dict)

                self._read_data(CDF.READONLY, config_def,
                                def_dict, default=False)
                
                cfg_def = ConfigDef(**def_dict.dict)
                if cfg_def.config_id not in config_def_dict:
                    config_def_dict[cfg_def.config_id] = cfg_def
                else:
                    raise ValueError(
                        f'Duplicate definition for {cfg_def.config_id} found.')

    def _read_data(self, cdf: CDF, source: dict, target: dict, default=None,  mandatory: bool = False) -> None:
        src_name = cdf.src_name
        if mandatory and src_name not in source:
            raise ValueError(
                f'Configuration definition: mandatory field "{src_name}" missing.')
        else:
            target.set(cdf, source.get(src_name, default))


    def __getitem__(self, key):
        return self.cfg_defs[key]

    def __setitem__(self, key, value):
        self.cfg_defs[key] = value

    def __delitem__(self, key):
        del self.cfg_defs[key]

    def __contains__(self, key):
        return key in self.cfg_defs

    def keys(self):
        return self.cfg_defs.keys()

    def values(self):
        return self.cfg_defs.values()

    def items(self):
        return self.cfg_defs.items()

    def __iter__(self):
        return iter(self.cfg_defs)

    def __len__(self):
        return len(self.cfg_defs)

    def get(self, key, default=None):
        if key in self.cfg_defs:
            return self.cfg_defs[key]
        return default            


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

    def get(self, property_name: str) -> Any:
        if property_name not in self.__dict__:
            raise KeyError(f'{property_name} invalid.')
        return self.__dict__.get(property_name)