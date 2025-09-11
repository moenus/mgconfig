# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import json
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hmac as _hmac, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional, Dict, Tuple
from enum import Enum
from dataclasses import dataclass
import base64


# === Crypto Parameters ===
AES_KEY_SIZE = 32        # 256-bit AES
SALT_SIZE = 32           # recommended HKDF salt size
NONCE_SIZE = 12          # AES-GCM recommended nonce size
MAX_SECRET_LEN = 1000    # maximum secret length in bytes

KDF_ALG = "HKDF-SHA256"
ITEMS_MAC_ALG = "HMAC-SHA256"
VERSION_STR = "v1"  # is used in file header and info parameter


# --------------------------------------------------------------------------------
# base64 string <--> bytes conversions
# --------------------------------------------------------------------------------

def bytes_to_b64str(value_bytes: bytes) -> str:
    """Convert bytes to a Base64-encoded UTF-8 string.

    Args:
        value_bytes (bytes): Arbitrary bytes.

    Returns:
        str: Base64-encoded string.
    """
    return base64.b64encode(value_bytes).decode('utf-8')


def b64str_to_bytes(value_str: str) -> bytes:
    """Convert a Base64-encoded string to bytes.

    Args:
        value_str (str): Base64-encoded string.

    Returns:
        bytes: Decoded bytes.
    """
    return base64.b64decode(value_str)


# --------------------------------------------------------------------------------
# hash bytes and return base64 string
# --------------------------------------------------------------------------------


def hash_bytes(value: bytes) -> str:
    """Compute a SHA-256 hash of input bytes, Base64-encoded.

    Args:
        value (bytes): Input data to hash.

    Returns:
        str: Base64-encoded SHA-256 digest of the input.
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(value)
    return bytes_to_b64str(digest.finalize())


# --------------------------------------------------------------------------------
# salt and master key generation
# --------------------------------------------------------------------------------

def generate_salt_str() -> str:
    """Generate a random salt for HKDF, Base64-encoded.

    Returns:
        str: Randomly generated salt encoded as a Base64 string.
    """
    return _generate_key_str(SALT_SIZE)


def generate_master_key_str() -> str:
    """Generate a random AES-256 master key, Base64-encoded.

    Returns:
        str: Randomly generated master key encoded as a Base64 string.
    """
    return _generate_key_str(AES_KEY_SIZE)


def _generate_key_str(key_size: int) -> str:
    """Generate a random key of given size, Base64-encoded.

    Args:
        key_size (int): Size of the key in bytes.

    Returns:
        str: Randomly generated key encoded as a Base64 string.
    """
    return bytes_to_b64str(os.urandom(key_size))


# --------------------------------------------------------------------------------
# key type definitions: AES or MAC
# --------------------------------------------------------------------------------
@dataclass(frozen=True)
class KeyTypeDef:
    """Key type definition for derived keys using HKDF."""
    name: str
    alg: str
    info: bytes
    key_size: int

    def derive_key(self, master_key: bytes, salt: bytes) -> bytes:
        """Derive a key from the master key using HKDF-SHA256.

        Args:
            master_key (bytes): Master key material.
            salt (bytes): Salt used for HKDF derivation.

        Returns:
            bytes: Derived key of length `self.key_size`.
        """
        hkdf = HKDF(algorithm=hashes.SHA256(), length=self.key_size,
                    salt=salt, info=self.info)
        return hkdf.derive(master_key)


class KeyType(Enum):
    AES = KeyTypeDef(name='aes',
                     alg='AESGCM',
                     info=("SecureStore|enc-key|"+VERSION_STR).encode(),
                     key_size=32)
    MAC = KeyTypeDef(name='mac',
                     alg='HMAC-SHA256',
                     info=("SecureStore|mac-key|"+VERSION_STR).encode(),
                     key_size=32)


class CryptoContextAES:
    """AES-GCM encryption/decryption context with associated data (AAD)."""

    def __init__(self, name: str, version: str, salt: bytes, master_key: bytes):
        """Initialize AES crypto context.

        Args:
            name (str): Identifier for the secret (used in AAD).
            version (str): Version string for AAD construction.
            salt (bytes): Salt value for key derivation.
            master_key (bytes): Master key material.
        """
        self._master_key = master_key
        self._name = name
        self._version = version
        self._salt = salt

    @property
    def _aad(self) -> bytes:
        return f"SecureStore:{self._version}|{bytes_to_b64str(self._salt)}|{self._mk_hash_str}|{self._name}".encode()

    @property
    def _mk_hash_str(self) -> str:
        return hash_bytes(self._master_key)

    @property
    def _aes_key(self) -> bytes:
        key_type_def = KeyType.AES.value
        return key_type_def.derive_key(self._master_key, self._salt)

    def encrypt(self, value: str) -> Tuple[str, str]:
        """Encrypt a string value with AES-GCM.

        Args:
            value (str): Plaintext value to encrypt.

        Returns:
            Tuple[str, str]: A tuple of (nonce_base64, ciphertext_base64).

        Raises:
            ValueError: If the plaintext exceeds `MAX_SECRET_LEN`.
        """
        value_bytes = str(value).encode("utf-8")
        if len(value_bytes) > MAX_SECRET_LEN:
            raise ValueError("value too large")
        nonce = os.urandom(NONCE_SIZE)
        ct = AESGCM(self._aes_key).encrypt(nonce, value_bytes, self._aad)
        return bytes_to_b64str(nonce), bytes_to_b64str(ct)

    def decrypt(self, nonce_b64: str, ct_b64: str) -> str:
        """Decrypt a value using AES-GCM.

        Args:
            nonce_b64 (str): Base64-encoded nonce.
            ct_b64 (str): Base64-encoded ciphertext.

        Returns:
            str: Decrypted plaintext string.

        Raises:
            cryptography.exceptions.InvalidTag: If authentication fails.
        """
        nonce = b64str_to_bytes(nonce_b64)
        ct = b64str_to_bytes(ct_b64)
        pt = AESGCM(self._aes_key).decrypt(nonce, ct, self._aad)
        return pt.decode("utf-8")


class CryptoContextMAC:
    """HMAC-SHA256 integrity protection context for items."""

    def __init__(self, salt: bytes, master_key: bytes):
        """Initialize MAC crypto context.

        Args:
            salt (bytes): Salt value for key derivation.
            master_key (bytes): Master key material.
        """
        self._master_key = master_key
        self._salt = salt

    @property
    def _mac_key(self) -> bytes:
        key_type_def = KeyType.MAC.value
        return key_type_def.derive_key(self._master_key, self._salt)

    def compute_items_mac(self, items: Dict[str, Dict[str, str]]) -> str:
        """Compute an integrity MAC for a set of items.

        Args:
            items (Dict[str, Dict[str, str]]): Items to protect.

        Returns:
            str: Base64-encoded HMAC-SHA256 digest of the canonicalized items.
        """
        h = _hmac.HMAC(self._mac_key, hashes.SHA256())
        h.update(self._canonicalize_items(items))
        return bytes_to_b64str(h.finalize())

    def verify_items_mac(self, items: Dict[str, Dict[str, str]], mac_b64: str) -> None:
        """Verify the integrity MAC for a set of items.

        Args:
            items (Dict[str, Dict[str, str]]): Items to verify.
            mac_b64 (str): Base64-encoded expected HMAC-SHA256 value.

        Raises:
            cryptography.exceptions.InvalidSignature: If MAC verification fails.
        """
        h = _hmac.HMAC(self._mac_key, hashes.SHA256())
        h.update(self._canonicalize_items(items))
        h.verify(b64str_to_bytes(mac_b64))

    def _canonicalize_items(self, items: Dict[str, Dict[str, str]]) -> bytes:
        """Canonicalize items to JSON for deterministic HMAC computation.

        Args:
            items (dict[str, dict[str, str]]): Dictionary of items.

        Returns:
            bytes: Canonical JSON encoding of items.
        """
        """Canonical JSON for deterministic HMAC (sorted keys, tight separators)."""
        return json.dumps(items, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
