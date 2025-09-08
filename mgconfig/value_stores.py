# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import yaml
from .config_key_map import ConfigKeyMap, APP, SEC
from .config_logger import config_logger
from .singleton_meta import SingletonMeta
from .secure_store import SecureStore
from .key_provider import KeyProvider
from .config_defs import CDF, ConfigDefs
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from enum import Enum
from pathlib import Path
from abc import abstractmethod
from .config_items import config_items
from .file_cache import FileCache, FileFormat, FileMode


config_configfile = ConfigKeyMap(APP, 'configfile')
config_securestorefile = ConfigKeyMap(SEC, 'securestore_file')


class ConfigValueSource(str, Enum):
    """Enumerates the possible configuration value sources."""

    CFGFILE = 'cfgfile'
    ENV_VAR = 'env_var'
    DEFAULT = 'default'
    ENCRYPT = 'encrypt'

    def __str__(self) -> str:
        return self.value


class ValueStore (metaclass=SingletonMeta):
    """Abstract base class for configuration value storage backends.

    Subclasses must implement both `save_value` and `retrieve_value`.
    """

    def __init__(self, source: ConfigValueSource):
        """Initializes a value store.

        Args:
            source (ConfigValueSource): The source type of configuration values
                (e.g., CFGFILE, ENV_VAR, DEFAULT, ENCRYPT).
        """
        if self._initialized:
            return  # avoid re-initializing
        self._initialized = True
        self._source = source

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


class ValueStoreSecure(ValueStore):
    """Value store for securely storing sensitive data in a secure store file."""

    def __init__(self):
        """Initialize a file-based secure value store for storing secret strings like passwords.
        """
        super().__init__(ConfigValueSource.ENCRYPT)
        self.securestore_file = config_items.get(
            config_securestorefile.id).value
        # initialize key provider with the configuration values from Configuration object
        self.key_provider = KeyProvider()
        try:
            secure_store = self._get_new_secure_store()
            if not secure_store.validate_master_key():
                config_logger.info(
                    'Secure store corrupted or master key invalid.')
            else:
                config_logger.info('Secure store successfully initialized.')
        except Exception as e:
            config_logger.error(f'Cannot initialize secure store: {e}')

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
            config_logger.info(f'Secret {item_id} saved to keystore.')
            return True
        except Exception as e:
            config_logger.error(
                f'Cannot store secret value for id {item_id}: {e}')
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
            return secure_store.retrieve_secret(item_id), self._source
        except Exception as e:
            config_logger.error(
                f'Cannot retrieve secret value for id {item_id}: {e}')
            return None, self._source

    def prepare_new_masterkey(self) -> str:
        """Prepares a new master key for the secure store.

        Returns:
            Optional[str]: The prepared master key string, or None if failed.
        """
        try:
            secure_store = self._get_new_secure_store()
            new_masterkey_str = secure_store.prepare_auto_key_exchange()
        except Exception as e:
            config_logger.error(f'Cannot prepare new master key: {e}')
            return None
        config_logger.info(
            'New master key generated. Auto-key-exchange prepared.')
        return new_masterkey_str


class ValueStoreFile(ValueStore):
    """Value store that retrieves and stores configuration data in a YAML file."""

    def __init__(self):
        """Initializes a file-based value store.

        """
        super().__init__(ConfigValueSource.CFGFILE)
        self.config_file = Path(config_items.get_value(config_configfile.id))
        self.file_cache = FileCache(self.config_file, file_format=FileFormat.YAML, file_mode=FileMode.ATOMIC_WRITE)

    def retrieve_value(self, item_id: str) -> tuple[Any, ConfigValueSource]:
        """Retrieves a value from the YAML configuration file.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: The retrieved value (or None if not found)
            and the source type.
        """
        config_section = ConfigDefs().cfg_def_property(item_id, str(CDF.SECTION))
        config_name = ConfigDefs().cfg_def_property(item_id, str(CDF.NAME))
        data = self.file_cache.data
        if config_section in data and config_name in data[config_section]:
            return data[config_section][config_name], self._source
        return None, self._source

    def save_value(self, item_id, value) -> bool:
        """Saves a value to the YAML configuration file.

        Args:
            item_id (str): Identifier of the configuration item.
            value (Any): The value to store.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        config_section = ConfigDefs().cfg_def_property(item_id, str(CDF.SECTION))
        config_name = ConfigDefs().cfg_def_property(item_id, str(CDF.NAME))
        data = self.file_cache.data        
        if config_section not in data:
            data[config_section] = {}
        data[config_section][config_name] = value
        return self.file_cache.save()


class ValueStoreEnv(ValueStore):
    """Value store that retrieves configuration values from environment variables."""

    def __init__(self):
        """Initializes an environment-variable-based value store.

        """
        super().__init__(ConfigValueSource.ENV_VAR)

    def retrieve_value(self, item_id: str) -> tuple[Any, ConfigValueSource]:
        """Retrieves a value from an environment variable.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: The retrieved environment variable value
            (or None if not set) and the source type.
        """
        config_env = ConfigDefs().cfg_def_property(item_id, str(CDF.ENV))
        if config_env is not None:
            return os.getenv(config_env), self._source
        return None, self._source

    def save_value(self, item_id: str, value: Any) -> bool:
        """Raises NotImplementedError since environment variables are read-only."""
        raise NotImplementedError("Environment variable store is read-only")


class ValueStoreDefault(ValueStore):
    """Value store that retrieves default configuration values from definitions."""

    def __init__(self):
        """Initializes a value store with default values.

        """
        super().__init__(ConfigValueSource.DEFAULT)

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieves a default value from the configuration definition.

        Args:
            item_id (str): Identifier of the configuration item.

        Returns:
            tuple[Any, ConfigValueSource]: The default value (or None if not defined)
            and the source type.
        """
        config_default = ConfigDefs().cfg_def_property(item_id, str(CDF.DEFAULT))
        if config_default:
            return config_default, self._source
        return None, self._source

    def save_value(self, item_id: str, value: Any) -> bool:
        """Raises NotImplementedError since defaults are read-only."""
        raise NotImplementedError("Default value store is read-only")


def get_new_masterkey() -> str:
    """
    Prepare a new master key from the secure value store.
    This method interacts with the secure value store to generate 
    and return a fresh master key.

    Returns:
        str: A newly generated master key.
    """
    return ValueStoreSecure().prepare_new_masterkey()
