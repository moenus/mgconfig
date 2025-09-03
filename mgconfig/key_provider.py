# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.keystores import KeyStores
from mgconfig.helpers import ConfigKeyMap, SEC
from typing import Any, Dict
from .config_values import config_values


class Key:
    """Represents a key stored in a keystore with lazy retrieval.

    Attributes:
        keystore_name (str): The name of the keystore containing this key.
        item_name (str): The name of the item/key within the keystore.
        _item_value (Any | None): Cached value of the key.
    """

    def __init__(self, keystore_name: str, item_name: str) -> None:
        """Initializes a Key instance.

        Args:
            keystore_name (str): Name of the keystore.
            item_name (str): Name of the key item in the keystore.
        """
        self.keystore_name = keystore_name
        self.item_name = item_name
        self._item_value: Any | None = None

    @property
    def value(self) -> str:
        """Retrieves the key value, loading it from the keystore if not cached.

        Returns:
            str: The value of the key.

        Raises:
            ValueError: If the keystore cannot provide a value for the key.
        """
        if self._item_value is None:
            self._retrieve_key()
        return self._item_value

    @value.setter
    def value(self, item_value: str) -> None:
        """Sets the key value in both the keystore and local cache.

        Args:
            item_value (str): The new value to set in the keystore.
        """
        KeyStores.get(self.keystore_name).set(self.item_name, item_value)
        self._item_value = item_value

    def __str__(self) -> str:
        """Returns a string representation of the key value.

        Returns:
            str: The key value as a string.
        """
        return str(self._item_value)

    def _retrieve_key(self):
        """Fetches the key value from the keystore and caches it.

        Raises:
            ValueError: If the keystore cannot provide a value for the key.
        """
        self._item_value = KeyStores.get(
            self.keystore_name).get(self.item_name)
        if self._item_value is None:
            raise ValueError(
                f'Keystore {self.keystore_name} cannot provide a value for {self.item_name}.')


ITEM_NAME_TAG = 'item_name'
KEYSTORE_NAME_TAG = 'keystore'
CONFIGURED_KEYS = ['master_key']

key_config = {}

for key_name in CONFIGURED_KEYS:
    key_config[key_name] = {
        KEYSTORE_NAME_TAG: ConfigKeyMap(SEC, key_name + '_' + KEYSTORE_NAME_TAG),
        ITEM_NAME_TAG: ConfigKeyMap(SEC, key_name + '_' + ITEM_NAME_TAG)
    }


class KeyProvider:
    """Provides access to a set of predefined keys from configured keystores.

    Attributes:
        VALID_KEYS (list[str]): List of allowed key names.
        _keys (dict[str, Key]): Mapping of key names to Key instances.
    """

    def __init__(self) -> None:
        """Initializes the KeyProvider by loading keys from configuration.

        Args:
            config (Dict[str, str]): Configuration dictionary containing keystore info.

        Raises:
            ValueError: If a keystore name in configuration is invalid.
        """
        self._keys = {}

        for key_name in key_config:
            keystore_name = self._get_value(key_name, KEYSTORE_NAME_TAG)
            item_name =self._get_value(key_name, ITEM_NAME_TAG)
            if not KeyStores.contains(keystore_name):
                raise ValueError(
                    f'Invalid keystore name {keystore_name}')
            try:
                KeyStores.get(keystore_name).configure()
                self._keys[key_name] = Key(keystore_name, item_name)
            except Exception as e:
                raise ValueError(
                    f'Cannot find valid configuration for key {key_name}.')

    def _get_value(self, key_name, sub_tag: str):
            value_obj = config_values.get(
                key_config[key_name][sub_tag].id)
            if value_obj:
                return value_obj.value
            raise ValueError(
                    f'Cannot find valid configuration for id {key_config[key_name][sub_tag].id}.')

    def get(self, name: str) -> str:
        """Retrieves the value of a named key.

        Args:
            name (str): The key name to retrieve (must be in VALID_KEYS).

        Returns:
            str: The value of the key.

        Raises:
            KeyError: If the key is not found in the provider.
        """
        if name not in self._keys:
            raise KeyError(f"Key '{name}' not found in provider.")
        return self._keys.get(name).value

    def set(self, name: str, value) -> None:
        """Sets the value of a named key.

        Args:
            name (str): The key name to update.
            value: The new value for the key.

        Raises:
            KeyError: If the key is not found in the provider.
        """
        if name not in self._keys:
            raise KeyError(f"Key '{name}' not found in provider.")
        self._keys.get(name).value = value
