# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional, Sequence
from .keystore_classes import KeyStore, KeyStoreFile, KeyStoreKeyring, KeyStoreEnv


class KeyStores:
    """Registry of available keystore instances.

    This class is by purpose not thread save. If used in a multi-threading environment it requeires external syncronization.

    Provides a global container for keystore instances and helper
    methods to add, retrieve, and interact with them.
    """
    
    _ks_dict: Dict[str, KeyStore] = {}

    @classmethod
    def add(cls, ks: KeyStore) -> None:
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
    def get(cls, keystore_name: str) -> Optional[KeyStore]:
        """Retrieve a registered keystore.

        Args:
            name (str): Keystore name.

        Returns:
            Optional[KeyStore]: The keystore instance, or None if not found.
        """
        cls.check_keystore(keystore_name)
        return cls._ks_dict.get(keystore_name)

    @classmethod
    def get_key(cls, keystore_name: str, item_name: str) -> Optional[str]:
        """Retrieve a key from a registered keystore.

        Args:
            keystore_name (str): Keystore name.
            item_name (str): Item key.

        Returns:
            Optional[str]: Stored value, or None if not found.

        Raises:
            ValueError: If the keystore is not registered.
        """
        cls.check_keystore(keystore_name)
        key_store = cls._ks_dict.get(keystore_name)
        return key_store.get(item_name)

    @classmethod
    def set_key(cls, keystore_name: str, item_name: str, key: str) -> None:
        """Store a key in a registered keystore.

        Args:
            keystore_name (str): Keystore name.
            item_name (str): Item key.
            key (str): Value to store.

        Raises:
            ValueError: If the keystore is not registered.
        """
        cls.check_keystore(keystore_name)
        key_store = cls._ks_dict.get(keystore_name)
        key_store.set(item_name, key)

    @classmethod
    def contains(cls, name: str) -> bool:
        """Check if a keystore is registered.

        Args:
            name (str): Keystore name.

        Returns:
            bool: True if registered, False otherwise.
        """
        return name in cls._ks_dict


    @classmethod
    def check_keystore(cls, keystore_name: str) -> None:
        """Validate that a keystore is registered.

        Args:
            keystore_name (str): Keystore name.

        Raises:
            ValueError: If the keystore is not registered.
        """        
        if keystore_name not in cls._ks_dict:
            raise ValueError(
                f'Invalid keystore name {keystore_name}')

    @classmethod
    def list_keystores(cls) -> list[str]:
        """List names of registered keystores.

        Returns:
            Sequence[str]: List of registered keystore names.
        """        
        return list(cls._ks_dict.keys())



KeyStores.add(KeyStoreEnv())
KeyStores.add(KeyStoreFile())
KeyStores.add(KeyStoreKeyring())
