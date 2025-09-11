# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT
"""
Configuration Definitions Module.

This module provides data structures and parsing logic for configuration 
definitions used across the system. Config definitions are typically 
described in YAML files and define metadata such as name, type, default 
value, and environment variable mappings for configuration items.

Main components:
    * CDF: Enum of field names used in config definitions.
    * ConfigDef: Dataclass representing a validated config definition.
    * DefDict: Helper class for handling definition dictionaries with CDF keys.
    * ConfigDefs: Collection of config definitions, loaded from YAML files.
"""

from typing import Callable, Optional, Any, Union, Iterator
from dataclasses import dataclass
from .config_types import ConfigTypes
from .extension_system import DefaultFunctions, DefaultValues
import keyword
from pathlib import Path
from enum import Enum
from .singleton_meta import SingletonMeta
from .file_cache import FileCache, FileMode, FileFormat

CONFIG_PREFIX = 'config'


class CDF(Enum):
    """Enum of fields used in configuration definitions.

    Each member maps to a specific key that may be present in the YAML 
    definition file. The string representation of each member returns a 
    prefixed field name, e.g. ``config_name`` instead of ``CDF.NAME``.

    Attributes:
        SECTION (str): The configuration section this item belongs to.
        PREFIX (str): The prefix used to namespace configuration keys.
        NAME (str): The configuration name.
        ID (str): The computed unique identifier (prefix + name).
        TYPE (str): The configuration type (validated against ConfigTypes).
        READONLY (str): Boolean flag for immutability.
        ENV (str): Environment variable mapping.
        DEFAULT (str): Default value for the config.
        DESCRIPTION (str): Human-readable description.
        DEFAULT_FUNCTION (str): Name of a function to compute the default value.
    """
    SECTION = 'section'
    PREFIX = 'prefix'
    NAME = 'name'
    ID = 'id'
    TYPE = 'type'
    READONLY = 'readonly'
    ENV = 'env'
    DEFAULT = 'default'
    DESCRIPTION = 'description'
    DEFAULT_FUNCTION = 'default_function'

    def __str__(self) -> str:
        """Return the field name prefixed with ``config_``.

        Returns:
            str: The prefixed field name.
        """
        return f'{CONFIG_PREFIX}_{self.value}'

    @property
    def src_name(self) -> str:
        """Return the raw YAML field name associated with this enum member.

        Returns:
            str: The original YAML field name.
        """
        return self.value


@dataclass
class ConfigDef():
    """Representation of a single configuration definition.

    This dataclass validates identifiers, types, defaults, and field 
    integrity at initialization time.

    Attributes:
        config_id (str): Unique identifier of the config (prefix + name).
        config_type (str): The type of the config (validated against ConfigTypes).
        config_readonly (bool): Whether this config is immutable.
        config_name (str): The base name of the config.
        config_prefix (str): The prefix namespace for the config.
        config_section (str): The section/group this config belongs to.
        config_env (Optional[str]): Optional environment variable to map from.
        config_description (Optional[str]): Optional human-readable description.
        config_default (Any): Optional default value.

    Raises:
        ValueError: If validation fails (invalid identifier, type mismatch, etc.).
    """
    config_id: str
    config_type: str
    config_readonly: bool
    config_name: str
    config_prefix: str
    config_section: str
    config_env: Optional[str] = None
    config_description: Optional[str] = None
    config_default: Any = None

    def __post_init__(self) -> None:
        """Validate the configuration definition after initialization.

        Ensures identifiers are valid Python identifiers, the config type 
        is registered, the default value matches the type, and required 
        fields are provided.

        Raises:
            ValueError: If validation fails.
        """

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

    def __str__(self):
        return self.config_id

    def get_property(self, property_name: str) -> Any:
        """Retrieve a property value by its attribute name.

        Args:
            property_name (str): The attribute name to retrieve.

        Returns:
            Any: The corresponding property value.

        Raises:
            KeyError: If the property does not exist.
        """
        if property_name not in self.__dict__:
            raise KeyError(f'{property_name} invalid.')
        return self.__dict__.get(property_name)


class DefDict:
    """Wrapper around a dictionary for config definitions keyed by CDF fields.

    Provides safe access and validation for setting and getting values 
    using ``CDF`` enum members.
    """

    def __init__(self) -> None:
        """Initialize an empty definition dictionary."""
        self.dict = {}

    def get(self, cdf: CDF) -> str:
        """Retrieve a value for a given CDF key.

        Args:
            cdf (CDF): The CDF enum key.

        Returns:
            str: The stored string value.

        Raises:
            KeyError: If the key is not a CDF instance or not found.
        """

        if not isinstance(cdf, CDF):
            raise KeyError(f'{cdf} is not instance of CDF.')
        if str(cdf) not in self.dict:
            raise KeyError(f'{str(cdf)} not found.')
        return self.dict.get(str(cdf))

    def set(self, cdf, value: str) -> None:
        """Set a value for a given CDF key.

        Args:
            cdf (CDF): The CDF enum key.
            value (str): The string value to assign.

        Raises:
            KeyError: If the key is not a CDF instance.
        """
        if not isinstance(cdf, CDF):
            raise KeyError(f'{cdf} is not instance of CDF.')
        self.dict[str(cdf)] = value


class ConfigDefs(metaclass=SingletonMeta):
    """Collection of configuration definitions.

    Config definitions are loaded from one or more YAML files and stored 
    in an internal dictionary keyed by ``config_id``.

    Example YAML format:
        - section: general
          prefix: app
          configs:
            - name: port
              type: int
              default: 8080
              description: Application port

    Attributes:
        cfg_defs (dict[str, ConfigDef]): Dictionary mapping config_id to ConfigDef.
    """

    def __init__(self, cfg_defs_filepaths: Union[str, list[str]] = None) -> None:
        """Load configuration definitions from YAML files.

        Args:
            cfg_defs_filepaths (Union[str, list[str]]): Path or list of paths to 
                YAML config definition files.

        Raises:
            ValueError: If YAML format is invalid or definitions are duplicated.
        """
        if self._initialized:
            return  # avoid re-initializing
        self._initialized = True

        self.items = {}

        if isinstance(cfg_defs_filepaths, (str, Path)):
            cfg_defs_filepaths = [cfg_defs_filepaths]
        for path in map(Path, cfg_defs_filepaths):
            if not path.exists():
                raise ValueError(
                    f"Config file {path} not found.")                
            file_cache = FileCache(path, file_format=FileFormat.YAML, file_mode=FileMode.READONLY)
            cfg_def_data = file_cache.data
            if not isinstance(cfg_def_data, list):
                raise ValueError(
                    f"Invalid config format in {path}, expected a list.")
            self._parse_config_defs_data(cfg_def_data, self.items)

    def _parse_config_defs_data(self, config_defs_data: list, config_def_dict: dict) -> list:
        """Parse raw config definitions from YAML into ConfigDef instances.

        Args:
            config_defs_data (list): A list of section dictionaries from definition source file
            config_def_dict (dict): The target dictionary to store results.

        Raises:
            ValueError: If mandatory fields are missing, defaults are invalid, 
                or duplicate IDs are found.
        """
        for section in config_defs_data:
            for config_def in section.get('configs', []):
                target_def_dict = DefDict()
                for field in [CDF.SECTION, CDF.PREFIX]:
                    self._read_data(
                        field, section, target_def_dict,  mandatory=True)
                if target_def_dict.get(CDF.PREFIX).startswith('_') or target_def_dict.get(CDF.PREFIX) != target_def_dict.get(CDF.PREFIX).lower():
                    raise ValueError(
                        f'{target_def_dict.get(CDF.PREFIX)} is invalid section prefix.')

                for field in [CDF.NAME, CDF.TYPE]:
                    self._read_data(field, config_def,
                                    target_def_dict,  mandatory=True)
                target_def_dict.set(
                    CDF.NAME, target_def_dict.get(CDF.NAME).lower())
                target_def_dict.set(
                    CDF.ID, f"{target_def_dict.get(CDF.PREFIX)}_{target_def_dict.get(CDF.NAME)}")

                default_function_name = config_def.get(
                    CDF.DEFAULT_FUNCTION.src_name)
                if default_function_name and DefaultFunctions().contains(default_function_name):
                    default_function = DefaultFunctions().get(default_function_name)
                    if callable(default_function):
                        # execute default function
                        target_def_dict.set(CDF.DEFAULT, default_function())
                    else:
                        raise ValueError(
                            f'{default_function} is not callable.')
                else:
                    if target_def_dict.get(CDF.ID) in DefaultValues().dict.keys():
                        target_def_dict.set(CDF.DEFAULT, DefaultValues().get(
                            target_def_dict.get(CDF.ID)))
                    else:
                        self._read_data(
                            CDF.DEFAULT, config_def, target_def_dict)
                for field in [CDF.ENV, CDF.DESCRIPTION]:
                    self._read_data(field, config_def, target_def_dict)

                self._read_data(CDF.READONLY, config_def,
                                target_def_dict, default=False)

                cfg_def = ConfigDef(**target_def_dict.dict)
                if cfg_def.config_id not in config_def_dict:
                    config_def_dict[cfg_def.config_id] = cfg_def
                else:
                    raise ValueError(
                        f'Duplicate definition for {cfg_def.config_id} found.')

    def _read_data(self, cdf: CDF, source: dict, target: DefDict, default=None,  mandatory: bool = False) -> None:
        """Read a single field from a source dictionary into a DefDict.

        Args:
            cdf (CDF): The CDF field to read.
            source (dict): The source dictionary (YAML section/config).
            target (DefDict): The target DefDict to store the value.
            default (Any, optional): Default value if not present.
            mandatory (bool, optional): Whether the field must exist.

        Raises:
            ValueError: If a mandatory field is missing.
        """
        src_name = cdf.src_name
        if mandatory and src_name not in source:
            raise ValueError(
                f'Configuration definition: mandatory field "{src_name}" missing.')
        else:
            target.set(cdf, source.get(src_name, default))

    def __getitem__(self, key: str) -> ConfigDef:
        """Retrieve a ConfigDef by its config_id.

        Args:
            key (str): The config_id to retrieve.

        Returns:
            ConfigDef: The corresponding configuration definition.
        """
        return self.items[key]

    def __setitem__(self, key: str, value: ConfigDef) -> None:
        """Assign a ConfigDef by its config_id.

        Args:
            key (str): The config_id.
            value (ConfigDef): The configuration definition to store.
        """
        self.items[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a ConfigDef by its config_id.

        Args:
            key (str): The config_id to delete.
        """
        del self.items[key]

    def __contains__(self, key: str) -> bool:
        """Check if a ConfigDef exists for the given config_id.

        Args:
            key (str): The config_id.

        Returns:
            bool: True if present, False otherwise.
        """
        return key in self.items

    def keys(self) -> list:
        """Return all config_ids.

        Returns:
            list: A list-like view of all config_ids.
        """
        return self.items.keys()

    def values(self) -> list:
        """Return all ConfigDef values.

        Returns:
            list: A list-like view of all ConfigDef values.
        """
        return self.items.values()

    def items(self) -> dict:
        """Return all (config_id, ConfigDef) pairs.

        Returns:
            dict: A dictionary-like view of config_id to ConfigDef mappings.
        """
        return self.items.items()

    def __iter__(self) -> Iterator:
        """Iterate over config_ids in the collection.

        Returns:
            Iterator: An iterator over config_ids.
        """
        return iter(self.items)

    def __len__(self) -> int:
        """Return the number of config definitions.

        Returns:
            int: The number of entries in the collection.
        """
        return len(self.items)

    def get(self, key: str, default=None) -> ConfigDef:
        """Retrieve a ConfigDef by key with a default fallback.

        Args:
            key (str): The config_id to retrieve.
            default (Any, optional): Value to return if not found.

        Returns:
            ConfigDef | Any: The ConfigDef instance or the provided default.
        """
        return self.items.get(key, default)

    def cfg_def_property(self, item_id: str, property_name: str) -> Optional[str]:
        """Retrieves a configuration definition property for an item.

        Args:
            item_id (str): Identifier of the configuration item.
            property_name (str): The property name in the configuration definition.

        Returns:
            Optional[str]: The configuration definition property value, or None
            if not found.
        """

        if item_id not in self:
            raise ValueError(f'{item_id} not found in ConfigDefs.')
        cfg_def = self.get(item_id)
        if cfg_def is None:
            return None
        return cfg_def.get_property(property_name)

    @classmethod
    def reset(cls):
        cls.reset_instance()
