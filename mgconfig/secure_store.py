# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


import os
import json
import uuid
import time
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hmac as _hmac, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path
from mgconfig.helpers import logger
from mgconfig.key_provider import KeyProvider
from cryptography.exceptions import InvalidTag
from dataclasses import dataclass, fields
from typing import Optional, Dict
from .secure_store_helpers import open_secure_file, bytes_to_b64str, b64str_to_bytes, hash_bytes, generate_key_str
from enum import Enum
from collections import namedtuple

__version__ = 1  # is used in file header and info parameter

# The implementation is not resistant to memory forensics.
# There is by design no backup mechanism for the secure file on disk.
# The master key is provided from a key store.

# === Crypto Constants ===
AES_KEY_SIZE = 32          # 32 bytes = 256 bits for AES-256
NONCE_SIZE = 12    # 12 bytes = recommended nonce size for AES-GCM
SALT_SIZE = 32  # 32 bytes = recommended salt size for HKDF

KeyParams = namedtuple("KeyParams", ['name', 'alg', 'info', 'key_size'])


class KeyType(Enum):
    AES = KeyParams(name='aes',
                    alg='AESGCM',
                    info=b"SecureStore|enc-key|v"+str(__version__).encode(),
                    key_size=32)
    MAC = KeyParams(name='mac',
                    alg='HMAC-SHA256',
                    info=b"SecureStore|mac-key|v"+str(__version__).encode(),
                    key_size=32)


KDF_ALG = "HKDF-SHA256"
ITEMS_MAC_ALG = "HMAC-SHA256"

# current master key encrypted with the new master key
AUTO_EXCHANGE_OLD_MASTER_KEY = '_aemk_old_k'

MAX_SECRET_LEN = 1000

ITEMNAME_NONCE = 'n'
ITEMNAME_CIPHERTEXT = 'ct'


@dataclass
class StoreHeader:
    version: int
    kdf: str
    salt_b64: str
    created_at: int
    mk_hash: str
    items_mac_b64: Optional[str] = None     # Base64(HMAC(items))
    items_mac_alg: Optional[str] = ITEMS_MAC_ALG





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
        self.master_key_str = key_provider.get('master_key')
        self._salt = None  # loaded from file or generated
        self._mk_validated = False
        self._dirty = False

        self._header: Optional[StoreHeader] = None
        self._items: Dict[str, Dict[str, str]] = {}
        if self.securestore_file.exists():
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
        try:
            with open(self.securestore_file, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load secure store: {e}")
            raise

        h = obj.get("_header", {})
        for field in fields(StoreHeader):
            if field.name not in h:
                raise ValueError(f"SecureStore header missing '{field.name}'")
        self._header = StoreHeader(**h)
        self._salt = b64str_to_bytes(self._header.salt_b64)

        self._items = obj.get("items", {})
        self._dirty = False

    def _ssf_create(self) -> None:
        self._salt = os.urandom(SALT_SIZE)  # public, random, per-store
        self._header = StoreHeader(
            version=__version__,
            kdf=KDF_ALG,
            salt_b64=bytes_to_b64str(self._salt),
            created_at=int(time.time()),
            mk_hash=self.master_key_hash,
            items_mac_b64=None,
            items_mac_alg=ITEMS_MAC_ALG
        )
        self._items = {}
        self._ssf_save(force=True)

    def _ssf_save(self, force: bool = False) -> None:
        """Write secure store atomically to disk.

        Ensures restrictive permissions (0600) and atomic replacement.
        """
        if not force and not self._dirty:
            return  # writing file skipped because not dirty and not forced
        parent_dir = Path(self.securestore_file).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        # always compute and set MAC
        self._header.items_mac_b64 = self.compute_items_mac(self._items)
        self._header.items_mac_alg = ITEMS_MAC_ALG

        obj = {"_header": self._header.__dict__, "items": self._items}
        data = json.dumps(obj, ensure_ascii=False,
                          separators=(",", ":")).encode("utf-8")
        tmp = self.securestore_file.with_suffix(f".tmp-{uuid.uuid4().hex}")

        # open securely (cross-platform)
        with open_secure_file(tmp, "w+b") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace
        os.replace(tmp, self.securestore_file)

    def _ssf_delete(self) -> None:
        """Delete the secure store file and clear sensitive data from memory."""
        self._items.clear()
        self._header = None
        self._salt = None
        if self.securestore_file.exists():
            self.securestore_file.unlink()

# --------------------------------------------------------------------------------
# derive keys
# --------------------------------------------------------------------------------

    def _key(self, key_type: KeyType) -> bytes:
        """Derive a key from the master key using HKDF-SHA256.

        Returns:
            bytes: Derived key of requested key type.
        """
        key_params = key_type.value
        hkdf = HKDF(algorithm=hashes.SHA256(), length=key_params.key_size,
                    salt=self._salt, info=key_params.info)
        return hkdf.derive(self._master_key)


# --------------------------------------------------------------------------------
# other functions
# --------------------------------------------------------------------------------


    def _aad(self, name: str) -> bytes:
        """Construct additional authenticated data (AAD) for AEAD encryption.

        Binds store version, salt, master key hash, and entry name to prevent tampering.

        Args:
            name (str): Secret entry name.

        Returns:
            bytes: Encoded AAD string.
        """
        return f"SecureStore:v{self._header.version}|{self._header.salt_b64}|{self._header.mk_hash}|{name}".encode()

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
            if not self._header.items_mac_b64:
                raise ValueError(
                    "SecureStore integrity check failed (items MAC missing)")

            if not self.verify_items_mac(self._items, self._header.items_mac_b64):
                raise ValueError(
                    "SecureStore integrity check failed (items MAC mismatch)")
            else:
                return True

        old_master_key_str = self.retrieve_secret(AUTO_EXCHANGE_OLD_MASTER_KEY)
        if old_master_key_str is None or self._header.mk_hash != hash_bytes(b64str_to_bytes(old_master_key_str)):
            return False

        new_master_keystr = self.master_key_str
        self.master_key_str = old_master_key_str

        if not self.verify_items_mac(self._items, self._header.items_mac_b64):
            raise ValueError(
                "SecureStore integrity check failed (items MAC mismatch)")

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
        value_bytes = str(value).encode("utf-8")
        if len(value_bytes) > MAX_SECRET_LEN:
            raise ValueError("value too large")
        key = self._key(KeyType.AES)
        nonce = os.urandom(NONCE_SIZE)
        ct = AESGCM(key).encrypt(nonce, value_bytes, self._aad(name))
        self._items[name] = {ITEMNAME_NONCE: bytes_to_b64str(
            nonce), ITEMNAME_CIPHERTEXT: bytes_to_b64str(ct)}
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
            key = self._key(KeyType.AES)
            nonce = b64str_to_bytes(entry[ITEMNAME_NONCE])
            ct = b64str_to_bytes(entry[ITEMNAME_CIPHERTEXT])
            pt = AESGCM(key).decrypt(nonce, ct, self._aad(name))
            return pt.decode("utf-8")
        except InvalidTag as e:
            logger.error(f"Decryption failed for {name}: {e}")
            return None
        except Exception as e:
            logger.error("Unexpected decryption error")
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
        new_master_key_str = generate_key_str()

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
        self.store_all_secrets(unencrypted_values)
        self._header.mk_hash = self.master_key_hash
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

# --------------------------------------------------------------------------------
# functions for HMAC creation and validation
# --------------------------------------------------------------------------------

    @staticmethod
    def _canonicalize_items(items: Dict[str, Dict[str, str]]) -> bytes:
        """Canonical JSON for deterministic HMAC (sorted keys, tight separators)."""
        return json.dumps(items, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")

    def compute_items_mac(self, items: Dict[str, Dict[str, str]]) -> str:
        """Compute an integrity HMAC over all items for integrity protection.
        
        Args:
            items (dict[str, dict[str, str]]): Items to be protected.

        Returns:
            str: Base64-encoded HMAC-SHA256 over the canonicalized items.
        """        
        mac_key = self._key(KeyType.MAC)
        h = _hmac.HMAC(mac_key, hashes.SHA256())
        h.update(self._canonicalize_items(items))
        mac = h.finalize()
        return bytes_to_b64str(mac)

    def verify_items_mac(self, items: Dict[str, Dict[str, str]], mac_b64: str) -> bool:
        """Verify the HMAC over all items; returns True if valid, False otherwise."""
        if not mac_b64:
            return False
        mac_key = self._key(KeyType.MAC)
        h = _hmac.HMAC(mac_key, hashes.SHA256())
        h.update(self._canonicalize_items(items))
        try:
            h.verify(b64str_to_bytes(mac_b64))
            return True
        except Exception:
            return False
