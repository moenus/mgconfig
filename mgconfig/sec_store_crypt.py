# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


import os
import json
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hmac as _hmac, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional, Dict, Tuple
from .sec_store_helpers import bytes_to_b64str, b64str_to_bytes
from enum import Enum
from collections import namedtuple

KDF_ALG = "HKDF-SHA256"
ITEMS_MAC_ALG = "HMAC-SHA256"
NONCE_SIZE = 12    # 12 bytes = recommended nonce size for AES-GCM
MAX_SECRET_LEN = 1000
# === Crypto Constants ===
AES_KEY_SIZE = 32          # 32 bytes = 256 bits for AES-256
SALT_SIZE = 32  # 32 bytes = recommended salt size for HKDF

__version__ = 1  # is used in file header and info parameter


def hash_bytes(value: bytes) -> str:
    """Compute a SHA-256 hash of input bytes, Base64-encoded.

    Args:
        value (bytes): Data to hash.

    Returns:
        str: Base64 SHA-256 digest.
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(value)
    return bytes_to_b64str(digest.finalize())



def generate_salt_str() -> str:
    return _generate_key_str(SALT_SIZE)

def generate_master_key_str() -> str:
    return _generate_key_str(AES_KEY_SIZE)


def _generate_key_str(key_size: int) -> str:
    """Generate a random AES-256 key, Base64-encoded.

    Returns:
        str: A randomly generated AES key encoded as a Base64 string.
    """
    return bytes_to_b64str(os.urandom(key_size))



# --------------------------------------------------------------------------------
# key type definitions: AES or MAC
# --------------------------------------------------------------------------------


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

# --------------------------------------------------------------------------------
# derive keys
# --------------------------------------------------------------------------------


def _derive_key(key_type: KeyType, master_key: bytes, salt: bytes) -> bytes:
    key_params = key_type.value
    hkdf = HKDF(algorithm=hashes.SHA256(), length=key_params.key_size,
                salt=salt, info=key_params.info)
    return hkdf.derive(master_key)

# --------------------------------------------------------------------------------
# aad
# --------------------------------------------------------------------------------


def _aad(name: str, version:str, salt_b64:str, mk_hash:str) -> bytes:
    return f"SecureStore:v{version}|{salt_b64}|{mk_hash}|{name}".encode()


# --------------------------------------------------------------------------------
# AES encryption and decryption
# --------------------------------------------------------------------------------

def sec_encrypt(name: str, value: str, master_key: bytes, version:str, salt_b64:str, mk_hash:str) -> Tuple[str, str]:
    value_bytes = str(value).encode("utf-8")
    if len(value_bytes) > MAX_SECRET_LEN:
        raise ValueError("value too large")
    key = _derive_key(KeyType.AES, master_key, b64str_to_bytes(salt_b64))
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(key).encrypt(nonce, value_bytes, _aad(name, version, salt_b64, mk_hash))
    return bytes_to_b64str(nonce), bytes_to_b64str(ct)


def sec_decrypt(name: str, master_key: bytes, version:str, salt_b64:str, mk_hash:str, nonce_b64: str, ct_b64: str) -> str:
    key = _derive_key(KeyType.AES, master_key, b64str_to_bytes(salt_b64))
    nonce = b64str_to_bytes(nonce_b64)
    ct = b64str_to_bytes(ct_b64)
    pt = AESGCM(key).decrypt(nonce, ct, _aad(name, version, salt_b64, mk_hash))
    return pt.decode("utf-8")


# --------------------------------------------------------------------------------
# functions for HMAC creation and validation
# --------------------------------------------------------------------------------

def _canonicalize_items(items: Dict[str, Dict[str, str]]) -> bytes:
    """Canonical JSON for deterministic HMAC (sorted keys, tight separators)."""
    return json.dumps(items, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def compute_items_mac(items: Dict[str, Dict[str, str]], master_key: bytes, salt_b64:str) -> str:
    """Compute an integrity HMAC over all items for integrity protection.

    Args:
        items (dict[str, dict[str, str]]): Items to be protected.

    Returns:
        str: Base64-encoded HMAC-SHA256 over the canonicalized items.
    """
    mac_key = _derive_key(KeyType.MAC, master_key, b64str_to_bytes(salt_b64))
    h = _hmac.HMAC(mac_key, hashes.SHA256())
    h.update(_canonicalize_items(items))
    mac = h.finalize()
    return bytes_to_b64str(mac)


def verify_items_mac(items: Dict[str, Dict[str, str]], mac_b64: str, master_key: bytes, salt_b64:str) -> bool:
    """Verify the HMAC over all items; returns True if valid, False otherwise."""
    if not mac_b64:
        return False
    mac_key = _derive_key(KeyType.MAC, master_key, b64str_to_bytes(salt_b64))
    h = _hmac.HMAC(mac_key, hashes.SHA256())
    h.update(_canonicalize_items(items))
    try:
        h.verify(b64str_to_bytes(mac_b64))
        return True
    except Exception:
        return False
