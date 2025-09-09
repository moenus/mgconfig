# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


from pathlib import Path
from mgconfig.key_provider import KeyProvider
from typing import Optional, Dict, Tuple
from .file_cache import FileCache, FileFormat, FileMode
from .sec_store_crypt import hash_bytes, generate_master_key_str, CryptoContextAES, bytes_to_b64str, b64str_to_bytes
from .sec_store_header import  SecurityHeader

import logging
logger = logging.getLogger(__name__)


# The implementation is not resistant to memory forensics.
# There is by design no backup mechanism for the secure file on disk.
# The master key is provided from a key store.


# current master key encrypted with the new master key
AUTO_EXCHANGE_OLD_MASTER_KEY = '_aemk_old_k'

ITEMNAME_NONCE = 'n'
ITEMNAME_CIPHERTEXT = 'ct'


class SecureStore:
    """Encrypted key–value store with integrity protection.

    Secrets are encrypted with AES-256-GCM using keys derived from a 
    master key via HKDF-SHA256. Store integrity is ensured by an HMAC 
    over all items. Automatic master key rotation is supported.

    Attributes:
        securestore_file (Path): Path to the secure store JSON file.
        _header (Optional[StoreHeader]): Metadata header for the store.
        _items (dict[str, dict[str, str]]): Encrypted items keyed by name.
        _salt (Optional[bytes]): Random salt used for HKDF derivation.
        _dirty (bool): Whether the store has unsaved changes.
        _mk_validated (bool): Whether the current master key has been validated.

    Notes:
        - Not resistant to memory forensics.
        - No backup mechanism: losing the file means losing all secrets.
        - Requires a master key supplied by a KeyProvider.
    """

    def __init__(self, securestore_file: str, key_provider: KeyProvider):
        """Initialize the secure store.

        Args:
            securestore_file (str): Path to the JSON secure store file.
            key_provider (KeyProvider): Provides a Base64-encoded 'master_key'.
        """
        self.securestore_file = Path(securestore_file)
        self._file_cache = FileCache(
            self.securestore_file, FileFormat.JSON, FileMode.ATOMIC_WRITE)
        self.master_key_str = key_provider.get('master_key')
        self._mk_validated = False
        self._dirty = False

        self._header: Optional[SecurityHeader] = None
        self._items: Dict[str, Dict[str, str]] = {}

        data = self._file_cache.data  # read implicit data file
        if data != {}:
            self._ssf_load()
        else:
            self._ssf_create()
        self._mk_validated = self.validate_master_key()

# --------------------------------------------------------------------------------
# context manager methods
# --------------------------------------------------------------------------------

    def __enter__(self) -> "SecureStore":
        return self

    def __exit__(self, exc_type: Optional[type[BaseException]],
                 exc: Optional[BaseException],
                 tb: Optional[object]) -> None:
        if self._dirty:
            self._ssf_save()

# --------------------------------------------------------------------------------
# securestore_file (ssf) create, load, save, delete
# --------------------------------------------------------------------------------

    def _ssf_load(self) -> None:
        self._header = SecurityHeader.prepare(self._file_cache.data.get("_header", {}))
        self._items = self._file_cache.data.get("items", {})
        self._dirty = False

    def _ssf_create(self) -> None:
        self._header = SecurityHeader.create_new(self.master_key_hash)
        self._items = {}
        self._ssf_save(force=True)

    def _ssf_save(self, force: bool = False) -> None:
        """Write secure store atomically to disk.

        Ensures restrictive permissions (0600) and atomic replacement.
        """
        if not force and not self._dirty:
            return  # writing file skipped because not dirty and not forced

        self._header.update_items_mac(self._items, self._master_key)

        self._file_cache.data["_header"] = self._header.__dict__
        self._file_cache.data["items"] = self._items
        self._file_cache.save()

    def _ssf_delete(self) -> None:
        """Delete the secure store file and clear sensitive data from memory."""
        self._items.clear()
        self._header = None
        if self.securestore_file.exists():
            self.securestore_file.unlink()
        self._file_cache.clear()


# --------------------------------------------------------------------------------
# other functions
# --------------------------------------------------------------------------------

    def validate_master_key(self) -> bool:
        """Validate the current master key against the stored hash.

        If the stored hash matches the current master key, also verify the
        items MAC. If validation fails but an old master key is available
        (from a prepared key exchange), perform automatic re-encryption
        using the new key.

        Returns:
            bool: True if the master key is valid or automatic key exchange succeeds.

        Raises:
            ValueError: If the store integrity check fails (missing or mismatched MAC).
        """
        if not self._header.items_mac_b64:
            raise ValueError(
                "SecureStore integrity check failed (items MAC missing)")

        if self._header.mk_hash == self.master_key_hash:
            self._header.verify_items_mac(self._items, self._master_key)                 
            return True

        old_master_key_str = self.retrieve_secret(AUTO_EXCHANGE_OLD_MASTER_KEY)
        if old_master_key_str is None or self._header.mk_hash != hash_bytes(b64str_to_bytes(old_master_key_str)):
            return False

        # key exchange requested

        new_master_keystr = self.master_key_str
        self.master_key_str = old_master_key_str

        self._header.verify_items_mac(self._items, self._master_key)    

        return self._auto_key_exchange(new_master_keystr)


# --------------------------------------------------------------------------------
# store, retrieve and delete items
# --------------------------------------------------------------------------------


    def store_secret(self, name: str, value: str) -> None:
        """
        Encrypt and store a single secret using AES-256-GCM.

        Args:
            name (str): Secret identifier.
            value (str): Secret plaintext.

        Raises:
            ValueError: If the secret exceeds MAX_SECRET_LEN.
        """
        crypt_context = CryptoContextAES(name, self._header.version, self._header.salt, self._master_key)
        nonce, ct = crypt_context.encrypt(value)
        self._items[name] = {ITEMNAME_NONCE: nonce, ITEMNAME_CIPHERTEXT: ct}        
        self._dirty = True

    def retrieve_secret(self, name: str) -> Optional[str]:
        """Decrypt a stored secret.

        Args:
            name (str): Secret name.

        Returns:
            Optional[str]: The decrypted secret value if successful, 
            or None if the secret does not exist or decryption fails.
        """

        entry = self._items.get(name)
        if not entry:
            return None
        try:
            crypt_context = CryptoContextAES(name, self._header.version, self._header.salt, self._master_key)  
            value = crypt_context.decrypt( entry[ITEMNAME_NONCE], entry[ITEMNAME_CIPHERTEXT])
            return value          
        except Exception as e:
            logger.error(f"Decryption failed for {name}: {e}")
            return None

    def delete_secret(self, name: str) -> bool:
        self._dirty = True
        return self._items.pop(name, None) is not None


# --------------------------------------------------------------------------------
# master key related properties
# --------------------------------------------------------------------------------


    @property
    def master_key_str(self) -> str:
        """Get the master key as a Base64-encoded string.

        Returns:
            str: Base64-encoded master key.
        """
        return bytes_to_b64str(self._master_key)

    @master_key_str.setter
    def master_key_str(self, keystring: str) -> None:
        """Set the master key from a Base64-encoded string.

        Args:
            keystring (str): Base64-encoded master key.
        """
        self._master_key = b64str_to_bytes(keystring)

    @property
    def master_key_hash(self) -> str:
        """Get the SHA-256 hash of the master key (Base64 encoded).

        Returns:
            str: Base64 hash string.
        """
        return hash_bytes(self._master_key)

# --------------------------------------------------------------------------------
# automatic key exchange mechanism
# --------------------------------------------------------------------------------

    def prepare_auto_key_exchange(self) -> str:
        """Prepare the secure store for an automatic key exchange.

        Generates a new master key, encrypts and stores the old one,
        and adds the hash of the new key.

        Returns:
            str: New master key (Base64 encoded).
        """
        logger.info(f'Prepare auto_key_exchange ...')

        current_mk_str = self.master_key_str
        new_master_key_str = generate_master_key_str()

        self.master_key_str = new_master_key_str
        self.store_secret(AUTO_EXCHANGE_OLD_MASTER_KEY, current_mk_str)

        self.master_key_str = current_mk_str
        self._ssf_save(force=True)
        logger.info(f'... auto_key_exchange prepared.')
        return new_master_key_str

    def _auto_key_exchange(self, new_master_key_str: str) -> bool:
        """Perform automatic master key exchange.

        Decrypts all items with the old key, re-encrypts with the new key,
        and updates the header.

        Returns:
            bool: True on success, False otherwise.
        """
        logger.info('Exchange master key ...')
        self.delete_secret(AUTO_EXCHANGE_OLD_MASTER_KEY)
        unencrypted_values = self.retrieve_all_secrets()

        self.master_key_str = new_master_key_str
        self._header.mk_hash = self.master_key_hash
        self.store_all_secrets(unencrypted_values)
        self._ssf_save(force=True)
        logger.info('Master key successfully exchanged.')
        return True

# --------------------------------------------------------------------------------
# functions to re-encrypt items for key-exchange
# --------------------------------------------------------------------------------

    def store_all_secrets(self, unencrypted_values: dict[str, str]) -> None:
        """
        Encrypt and store multiple secrets, overwriting any existing values.

        Args:
            unencrypted_values (dict[str, str]): Mapping of names to plaintext values.
        """

        logger.debug('store all secrets')
        for key in unencrypted_values:
            self.store_secret(key, str(unencrypted_values[key]))

    def retrieve_all_secrets(self) -> dict[str, str]:
        """Decrypt and return all stored secrets.

        Returns:
            dict: Mapping of entry names to plaintext values.
        """
        logger.debug('retrieve all secrets')
        unencrypted = {}
        for key in self._items:
            value = self.retrieve_secret(key)
            if value is not None:
                unencrypted[key] = value
        return unencrypted
