# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import keyring
import os

from pathlib import Path
from .config_key_map import ConfigKeyMap, SEC
from typing import Any, Dict, Optional, Sequence
from .config_items import config_items
from .file_cache import FileCache, FileFormat, FileMode


config_keyfile = ConfigKeyMap(SEC, 'keyfile_filepath')
config_service_name = ConfigKeyMap(SEC, 'keyring_service_name')


class KeyStore:
    """Abstract base class for different types of keystores.

    Provides a common interface for retrieving and storing secure data.
    Subclasses must implement the `get` method and may override `set`
    if writing is supported.

    Attributes:
        keystore_name (str): Human-readable name of the keystore type.
        params (Dict[str, Any]): Configuration parameters for the keystore.
        mandatory_config_items (Sequence[ConfigKeyMap]): Required configuration parameter definitions.
    """

    keystore_name = 'unknown'

    def __init__(self) -> None:
        """Initializes the keystore with empty parameters."""
        self.params: Dict[str, Any] = {}
        self.mandatory_config_items: Sequence[ConfigKeyMap] = []
        self._configured = False

    def get(self, name: str) -> Optional[str]:
        """Retrieve a value from the keystore.

        Args:
            name (str): The key name to retrieve.

        Returns:
            Optional[str]: The stored value, or None if not found.

        Raises:
            NotImplementedError: If not implemented in subclass.
        """
        raise NotImplementedError()

    def set(self, name: str, value: str) -> None:
        """Store a value in the keystore.

        Args:
            name (str): The key name.
            value (str): The value to store.

        Raises:
            ValueError: If the keystore type does not support writing.
        """
        raise ValueError(
            f'Cannot update keys in keystore {self.keystore_name}.')

    def get_param(self, name: str) -> Any:
        """Retrieve a configuration parameter value.

        Args:
            name (str): The parameter name.

        Returns:
            Any: The configuration parameter value.

        Raises:
            ValueError: If the parameter is missing from the configuration.
        """
        if name not in self.params:
            raise ValueError(
                f'Configuration item {name} for keystore {self.keystore_name} is missing.')
        return self.params[name]

    def prepare_params(self) -> None:
        """Load and validate required configuration parameters.

        Looks up values in the global ``config_items`` registry
        and assigns them to this keystore's parameters.

        Raises:
            ValueError: If any mandatory parameter is missing or None.
        """
        for config_key_map in self.mandatory_config_items:

            config_item = config_items.get(config_key_map.id)
            if config_item is None:
                raise ValueError(
                    f'Configuration ID {config_key_map.id} for keystore {self.keystore_name} not found.')
            self.params[config_key_map.id] = config_item.value
            if self.params[config_key_map.id] is None:
                raise ValueError(
                    f'Mandatory parameter {config_key_map.id} for keystore {self.keystore_name} not found.')

    def check_configuration(self) -> None:
        """Validate that the keystore has been properly configured.

        Raises:
            ValueError: If the keystore is not configured.
        """
        if len(self.params) == 0:
            raise ValueError(
                f'Keystore {self.keystore_name} is not configured properly.')


class KeyStoreFile(KeyStore):
    """File-based keystore implementation.

    Stores keys in a JSON file on disk.

    Attributes:
        filedata (dict[str, str]): In-memory storage of loaded key-value pairs.
    """
    keystore_name = 'file'

    def __init__(self) -> None:
        """Initialize the file-based keystore."""
        super().__init__()
        self._file_cache = None
        self.mandatory_config_items: Sequence[ConfigKeyMap] = [config_keyfile]

    @property
    def filepath(self) -> Path:
        """Path to the keystore file.

        Returns:
            Path: File path from configuration.
        """
        return Path(self.get_param(config_keyfile.id))

    def check_configuration(self) -> None:
        """Validate configuration and load file data if necessary.
        """
        if self._file_cache:
            return
        super().check_configuration()
        self._file_cache = FileCache(self.filepath, FileFormat.JSON, file_mode=FileMode.SECURE_WRITE)
        

    def get(self, item_name: str) -> Optional[str]:
        """Retrieve a value from the file-based keystore.

        Args:
            item_name (str): Key name.

        Returns:
            Optional[str]: Stored value, or None if not found.
        """
        self.check_configuration()
        return self._file_cache.data.get(item_name, None)

    def set(self, item_name: str, value: str) -> None:
        """Store a value in the file-based keystore.

        Args:
            item_name (str): Key name.
            value (str): Value to store.
        """
        self.check_configuration()
        self._file_cache.data[item_name] = value
        self._file_cache.save()


class KeyStoreKeyring(KeyStore):
    """Keyring-based keystore implementation.

    Uses the system keyring service for storing secure data.
    """
    keystore_name = 'keyring'

    def __init__(self) -> None:
        """Initialize the keyring-based keystore."""
        super().__init__()
        self.mandatory_config_items: Sequence[ConfigKeyMap] = [
            config_service_name]
        self._configured = True

    @property
    def service_name(self) -> str:
        """Retrieve the configured keyring service name.

        Returns:
            str: Service name.
        """
        return self.get_param(config_service_name.id)

    def get(self, item_name: str) -> Optional[str]:
        """Retrieve a value from the keyring.

        Args:
            item_name (str): Key name.

        Returns:
            Optional[str]: Stored value, or None if not found.

        Raises:
            KeyError: If retrieval from the keyring fails.
        """
        self.check_configuration()
        try:
            return keyring.get_password(
                self.service_name, item_name)
        except Exception as e:
            raise KeyError(f'Cannot read from keyring for {item_name}: {e}')

    def set(self, item_name: str, value: str) -> None:
        """Store a value in the keyring.

        Args:
            item_name (str): Key name.
            value (str): Value to store.

        Raises:
            KeyError: If storing to the keyring fails.
        """
        self.check_configuration()
        try:
            keyring.set_password(self.service_name,
                                 item_name, value)
        except Exception as e:
            raise KeyError(f'Cannot write to keyring for {item_name}: {e}')


class KeyStoreEnv(KeyStore):
    """Environment variable-based keystore implementation.

    Retrieves keys from environment variables.
    """
    keystore_name = 'env'

    def get(self, item_name) -> Optional[str]:
        """Retrieve a value from environment variables.

        Args:
            item_name (str): Environment variable name.

        Returns:
            Optional[str]: Environment variable value, or None if not set.
        """
        value = os.getenv(item_name)
        return str(value) if value is not None else None
