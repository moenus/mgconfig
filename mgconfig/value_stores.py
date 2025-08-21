# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import yaml
from .helpers import logger, config_securestorefile, config_configfile
from .secure_store import SecureStore
from .key_provider import KeyProvider
from .config_defs import CDF, ConfigDefs
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod


class ConfigValueSource(str, Enum):
    """Enumerates the possible configuration value sources."""

    CFGFILE = 'cfgfile'
    ENV_VAR = 'env_var'
    DEFAULT = 'default'
    ENCRYPT = 'encrypt'


class ValueStore (ABC):
    """Abstract base class for configuration value storage backends.

    Subclasses must implement both `save_value` and `retrieve_value`.
    """

    def __init__(self, source: ConfigValueSource, cfg_defs: ConfigDefs):
        """Initializes a value store.

        Args:
            source (ConfigValueSource): The source type of configuration values
                (e.g., CFGFILE, ENV_VAR, DEFAULT, ENCRYPT).
            cfg_defs (ConfigDefs): Configuration definitions used for lookup.
        """
        self.source = source
        self.cfg_defs = cfg_defs


    @abstractmethod
    def save_value(self, item_id: str, value: Any) -> bool:
        """Saves a value in the store.

        Args:
            item_id (str): Identifier of the configuration item.
            value (Any): Value to store.

        Returns:
            bool: True if the value was saved successfully, False otherwise.

        Raises:
            NotImplementedError: If called on a read-only store.
        """
        pass

    @abstractmethod
    def retrieve_value(self, item_id: str) -> tuple[Any, ConfigValueSource]:
        """Retrieves a value from the store.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: A tuple containing the value (or None
            if not found) and the source type.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        pass

    def _get_cfg_def_value(self, item_id: str, property_name: str) -> Optional[str]:
        """Retrieves a configuration definition property for an item.

        Args:
            item_id (str): Identifier of the configuration item.
            property_name (str): The property name in the configuration definition.

        Returns:
            Optional[str]: The configuration definition property value, or None
            if not found.
        """
        if item_id in self.cfg_defs:
            return self.cfg_defs.get(item_id).get_property(property_name)


class ValueStoreSecure(ValueStore):
    """Value store for securely storing sensitive data in a secure store file."""

    def __init__(self, cfg_defs: ConfigDefs, init_config: Dict[str, str] = None):
        """Initialize a file-based secure value store for storing secret strings like passwords.

        Args:
            cfg_defs (ConfigDefs): Configuration definitions for lookup.
            init_config (Dict[str, str]): Initialization values containing paths
                and credentials for secure storage.
        """
        super().__init__(ConfigValueSource.ENCRYPT, cfg_defs)
        self.securestore_file = init_config.get(
            config_securestorefile.config_id)
        # initialize key provider with the configuration values from Configuration object
        self.key_provider = KeyProvider(init_config)
        try:
            secure_store = self._get_new_secure_store()
            if not secure_store.validate_master_key():
                logger.info(
                    'Master key invalid or secure store corrupted.')
            else:
                logger.info('Secure store was successfully initialized.')
        except Exception as e:
            logger.error(f'Cannot initialize secure store: {e}')

    def _get_new_secure_store(self) -> SecureStore:
        """Creates a new `SecureStore` instance.

        Returns:
            SecureStore: The initialized secure store.
        """
        return SecureStore(
            self.securestore_file,
            self.key_provider
        )

    def save_value(self, item_id: str, value: str) -> bool:
        """Saves a secret value securely.

        Args:
            item_id (str): Identifier of the configuration item.
            value (str): The secret value to store.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            secure_store = self._get_new_secure_store()
            secure_store.store_secret(item_id, value)
            secure_store._ssf_save()
            logger.info(f'Secret {item_id} saved to keystore.')
            return True
        except Exception as e:
            logger.error(f'Cannot store secret value for id {item_id}: {e}')
        return False

    def retrieve_value(self, item_id: str) -> tuple[Any, ConfigValueSource]:
        """Saves a secret value securely.

        Args:
            item_id (str): Identifier of the configuration item.
            value (str): The secret value to store.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            secure_store = self._get_new_secure_store()
            return secure_store.retrieve_secret(item_id), self.source
        except Exception as e:
            logger.error(f'Cannot retrieve secret value for id {item_id}: {e}')
            return None, self.source

    def prepare_new_masterkey(self) -> str:
        """Prepares a new master key for the secure store.

        Returns:
            Optional[str]: The prepared master key string, or None if failed.
        """
        try:
            secure_store = self._get_new_secure_store()
            new_masterkey_str = secure_store.prepare_auto_key_exchange()
        except Exception as e:
            logger.error(f'Cannot prepare new master key: {e}')
            return None
        logger.info('New master key generated. Auto-key-exchange prepared.')
        return new_masterkey_str


class ValueStoreFile(ValueStore):
    """Value store that retrieves and stores configuration data in a YAML file."""

    def __init__(self, cfg_defs: ConfigDefs, init_config: Dict[str, str] = None):
        """Initializes a file-based value store.

        Args:
            cfg_defs (ConfigDefs): Configuration definitions for lookup.
            init_config (Dict[str, str]): Initialization values containing the path
                to the configuration file.
        """
        super().__init__(ConfigValueSource.CFGFILE, cfg_defs)
        self.config_file = init_config.get(config_configfile.config_id)
        self.configfile_content = self._read_configfile()

    def _read_configfile(self) -> dict[str, Any]:
        """Reads configuration data from the YAML config file.

        Returns:
            dict: The contents of the configuration file.
                Returns an empty dict if the file does not exist or is empty.
        """
        if os.path.exists(self.config_file):
            logger.info(f'Reading config from file "{self.config_file}"')
            with open(self.config_file, "r") as file:
                # Use safe_load to prevent code execution
                return yaml.safe_load(file)
        else:
            logger.info(f'No config file "{self.config_file}" found.')
            return {}

    def retrieve_value(self, item_id: str) -> tuple[Any, ConfigValueSource]:
        """Retrieves a value from the YAML configuration file.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: The retrieved value (or None if not found)
            and the source type.
        """
        config_section = self._get_cfg_def_value(item_id, str(CDF.SECTION))
        config_name = self._get_cfg_def_value(item_id, str(CDF.NAME))
        if config_section in self.configfile_content and config_name in self.configfile_content[config_section]:
            return self.configfile_content[config_section][config_name], self.source
        return None, self.source

    def save_value(self, item_id, value) -> bool:
        """Saves a value to the YAML configuration file.

        Args:
            item_id (str): Identifier of the configuration item.
            value (Any): The value to store.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        config_section = self._get_cfg_def_value(item_id, str(CDF.SECTION))
        config_name = self._get_cfg_def_value(item_id, str(CDF.NAME))
        if config_section not in self.configfile_content:
            self.configfile_content[config_section] = {}
        self.configfile_content[config_section][config_name] = value
        return self._write_configfile()

    def _write_configfile(self) -> bool:
        """Writes the current configuration to the YAML file.

        Returns:
            bool: True if the file was written successfully, False otherwise.
        """
        config_path = Path(self.config_file)
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(
                f"Directory '{config_path}' could not be prepared: {e}.")
            return False
        try:
            with open(self.config_file, "w") as file:
                yaml.dump(self.configfile_content, file,
                          default_flow_style=False)
            return True
        except Exception as e:
            logger.error(
                f"File '{self.config_file}' could not be written: {e}.")
            return False


class ValueStoreEnv(ValueStore):
    """Value store that retrieves configuration values from environment variables."""

    def __init__(self, cfg_defs: ConfigDefs, init_config: Dict[str, str] = None):
        """Initializes an environment-variable-based value store.

        Args:
            cfg_defs (ConfigDefs): Configuration definitions for lookup.
            init_config (Dict[str, str]): Optional initialization values.
        """
        super().__init__(ConfigValueSource.ENV_VAR, cfg_defs)

    def retrieve_value(self, item_id: str) -> tuple[Any, ConfigValueSource]:
        """Retrieves a value from an environment variable.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: The retrieved environment variable value
            (or None if not set) and the source type.
        """
        config_env = self._get_cfg_def_value(item_id, str(CDF.ENV))
        if config_env is not None:
            return os.getenv(config_env), self.source
        return None, self.source

    def save_value(self, item_id: str, value: Any) -> bool:
        """Raises NotImplementedError since environment variables are read-only."""        
        raise NotImplementedError("Environment variable store is read-only")


class ValueStoreDefault(ValueStore):
    """Value store that retrieves default configuration values from definitions."""

    def __init__(self, cfg_defs: ConfigDefs, init_config: Dict[str, str] = None):
        """Initializes a value store with default values.

        Args:
            cfg_defs (ConfigDefs): Configuration definitions for lookup.
            init_config (Dict[str, str]): Optional initialization values.
        """
        super().__init__(ConfigValueSource.DEFAULT, cfg_defs)

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieves a default value from the configuration definition.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: The default value (or None if not defined)
            and the source type.
        """
        config_default = self._get_cfg_def_value(item_id, str(CDF.DEFAULT))
        if config_default:
            return config_default, self.source
        return None, self.source

    def save_value(self, item_id: str, value: Any) -> bool:
        """Raises NotImplementedError since defaults are read-only."""        
        raise NotImplementedError("Default value store is read-only")


class ValueStores:
    """Factory and registry for initialized value store instances."""

    value_stores = {}

    @classmethod
    def _get(cls, value_store_class: Type[ValueStore], cfg_def_dict=None, init_config: Dict[str, str] = None):
        """Retrieve or initialize a value store instance.

        Args:
            value_store_class (Type[ValueStore]): The value store class to retrieve or initialize.
            init_config (Dict[str, str], optional): The initialization configuration. Required if the instance is not yet initialized.

        Returns:
            ValueStore: The initialized value store instance.

        Raises:
            ValueError: If the class is invalid or initialization fails.
        """
        if value_store_class in cls.value_stores:
            # this value store was already initialized
            return cls.value_stores.get(value_store_class)
        if not issubclass(value_store_class, ValueStore):
            raise ValueError(f'Value store class {value_store_class} invalid.')
        try:
            new_value_store = value_store_class(cfg_def_dict, init_config)
            cls.value_stores[value_store_class] = new_value_store
            return new_value_store
        except Exception as e:
            raise ValueError(
                f'Cannot initialize value store {value_store_class}! {e}')

    @classmethod
    def retrieve_val(cls, value_store_class: Type, config_id: str, cfg_defs: ConfigDefs, init_config: Dict[str, str] = None) -> Tuple[Any, Optional[str]]:
        """Retrieves a value from a specific value store.

        Args:
            value_store_class (Type[ValueStore]): The class of the value store
                (e.g., ValueStoreFile, ValueStoreEnv).
            config_id (str): Identifier of the configuration item.
            cfg_defs (ConfigDefs): Configuration definitions for lookup.
            init_config (Optional[Dict[str, str]]): Optional initialization
                configuration.

        Returns:
            tuple[Any, Optional[ConfigValueSource]]: Retrieved value and its
            source type. Returns (None, None) if the store could not be used.
        """
        value_store = cls._get(value_store_class, cfg_defs, init_config)
        return value_store.retrieve_value(config_id) if value_store else (None, None)

    @classmethod
    def save_val(cls, value_store_class: Type, config_id: str, value: Any) -> Tuple[Any, Optional[str]]:
        """Saves a value to a specific value store.

        Args:
            value_store_class (Type[ValueStore]): The class of the value store.
            config_id (str): Identifier of the configuration item.
            value (Any): The value to store.

        Returns:
            tuple[Any, Optional[str]]: The result of the save operation, or (None, None)
            if the store could not be used.
        """
        value_store = cls._get(value_store_class)
        return value_store.save_value(config_id, value) if value_store else (None, None)


def get_new_masterkey() -> str:
    """
    Prepare a new master key from the secure value store.
    This method interacts with the secure value store to generate 
    and return a fresh master key.

    Returns:
        str: A newly generated master key.
    """
    return ValueStores._get(ValueStoreSecure).prepare_new_masterkey()