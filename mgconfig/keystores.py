# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import keyring
import os
import json
from pathlib import Path
from .helpers import config_keyfile, config_service_name, ConstConfig, config_logger
from typing import Any, Dict, Optional
from .config_values import config_values


class KeyStore:
    """Base class for different types of keystores.

    Provides a common interface for retrieving and storing secure data.
    Subclasses must implement the `get` method and may override `set`
    if writing is supported.

    Attributes:
        keystore_name (str): Human-readable name of the keystore type.
        params (Optional[Dict[str, Any]]): Configuration parameters for the keystore.
        mandatory_conf_names (list): List of required configuration parameter names.
    """

    keystore_name = 'unknown'

    def __init__(self):
        """Initializes the keystore with empty parameters."""
        self.params: Optional[Dict[str, Any]] = None
        self.mandatory_conf_names = []

    def get(self, name: str) -> Optional[str]:
        """Retrieve a value from the keystore.

        Args:
            name (str): The key name to retrieve.

        Returns:
            Optional[str]: The stored value, or None if not found.
        """
        return

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

    def get_param(self, name: str):
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

    def configure(self):
        """Configure the keystore with required parameters.

        Args:
            config_params (Optional[Dict[str, Any]]): Configuration parameters.

        Raises:
            ValueError: If any mandatory parameter is missing.
        """
        self.params = {}

        for conf_name in self.mandatory_conf_names:
            const_config = ConstConfig(conf_name)
            config_value = config_values.get(const_config.config_id)
            if config_value is None:
                raise ValueError(
                    f'Configuration ID {const_config.config_id} for keystore {self.keystore_name} not found.')
            self.params[conf_name] = config_value.value
            if self.params[conf_name] is None:
                raise ValueError(
                    f'Mandatory parameter {conf_name} for keystore {self.keystore_name} not found.')

    def check_configuration(self):
        """Validate that the keystore has been properly configured.

        Raises:
            ValueError: If the keystore is not configured.
        """
        if self.params is None:
            raise ValueError(
                f'Keystore {self.keystore_name} is not configured properly.')


class KeyStoreFile(KeyStore):
    """File-based keystore implementation.

    Stores keys in a JSON file on disk.

    Attributes:
        filedata (dict): In-memory storage of loaded key-value pairs.
    """
    keystore_name = 'file'

    def __init__(self):
        """Initialize the file-based keystore."""
        super().__init__()
        self.filedata = None
        self.mandatory_conf_names = [config_keyfile.config_handle]

    @property
    def filepath(self):
        """Path to the keystore file.

        Returns:
            str: File path from configuration.
        """
        return self.get_param(config_keyfile.config_handle)

    def check_configuration(self):
        """Validate configuration and load file data if necessary.

        Raises:
            ValueError: If the keystore file is missing or empty.
        """
        super().check_configuration()
        if not self.filedata:
            self.filedata = {}
            if os.path.exists(self.filepath):
                with open(self.filepath, "r") as f:
                    self.filedata = json.load(f)
            if self.filedata is None or self.filedata == {}:
                raise ValueError(
                    f'Could not read keystore data from file {self.filepath}.')

    def get(self, item_name: str) -> str:
        """Retrieve a value from the file-based keystore.

        Args:
            item_name (str): Key name.

        Returns:
            Optional[str]: Stored value, or None if not found.
        """
        self.check_configuration()
        if self.filedata:
            return self.filedata.get(item_name)

    def set(self, item_name: str, value: str):
        """Store a value in the file-based keystore.

        Args:
            item_name (str): Key name.
            value (str): Value to store.
        """
        self.check_configuration()
        self.filedata[item_name] = value
        self._save()

    def _save(self):
        """Save in-memory key-value pairs to disk.

        Returns:
            bool: True if save was successful, False otherwise.
        """
        if not os.path.exists(self.filepath):
            path = Path(self.filepath).parent
            path.mkdir(parents=True, exist_ok=True)
        else:
            if not os.access(self.filepath, os.W_OK):
                return False
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.filedata, f)
            return True
        except Exception as e:
            config_logger.error(f'Cannot write to file {self.filepath}: {e}')
            return False


class KeyStoreKeyring(KeyStore):
    """Keyring-based keystore implementation.

    Uses the system keyring service for storing secure data.
    """
    keystore_name = 'keyring'

    def __init__(self):
        """Initialize the keyring-based keystore."""
        super().__init__()
        self.mandatory_conf_names = [config_service_name.config_handle]

    @property
    def service_name(self) -> str:
        """Retrieve the configured keyring service name.

        Returns:
            str: Service name.
        """
        return self.get_param(config_service_name.config_handle)

    def get(self, item_name: str) -> Optional[str]:
        """Retrieve a value from the keyring.

        Args:
            item_name (str): Key name.

        Returns:
            Optional[str]: Stored value, or None if not found.
        """
        self.check_configuration()
        return keyring.get_password(
            self.service_name, item_name)

    def set(self, item_name: str, value: str) -> None:
        """Store a value in the keyring.

        Args:
            item_name (str): Key name.
            value (str): Value to store.
        """
        self.check_configuration()
        keyring.set_password(self.service_name,
                             item_name, value)


class KeyStoreEnv(KeyStore):
    """Environment variable-based keystore implementation.

    Retrieves keys from environment variables.
    """
    keystore_name = 'env'

    def get(self, item_name):
        """Retrieve a value from environment variables.

        Args:
            item_name (str): Environment variable name.

        Returns:
            Optional[str]: Environment variable value, or None if not set.
        """
        return os.getenv(item_name)


class KeyStores:
    """Registry of available keystore instances."""
    _ks_dict = {}

    @classmethod
    def add(cls, ks: KeyStore):
        """Register a new keystore.

        Args:
            ks (KeyStore): Keystore instance to register.

        Raises:
            ValueError: If a keystore with the same name is already registered.
        """
        if ks.keystore_name in cls._ks_dict:
            raise ValueError(
                f"Keystore '{ks.keystore_name}' is already existing.")
        cls._ks_dict[ks.keystore_name] = ks

    @classmethod
    def get(cls, name: str) -> Optional[KeyStore]:
        """Retrieve a registered keystore.

        Args:
            name (str): Keystore name.

        Returns:
            Optional[KeyStore]: The keystore instance, or None if not found.
        """
        return cls._ks_dict.get(name)

    @classmethod
    def contains(cls, name: str) -> bool:
        """Check if a keystore is registered.

        Args:
            name (str): Keystore name.

        Returns:
            bool: True if registered, False otherwise.
        """
        return name in cls._ks_dict


KeyStores.add(KeyStoreEnv())
KeyStores.add(KeyStoreFile())
KeyStores.add(KeyStoreKeyring())
