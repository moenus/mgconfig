# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
from cryptography.exceptions import InvalidKey, InvalidTag, InvalidSignature
import json
import os

from mgconfig.sec_store_crypt import (
    hash_bytes, generate_salt_str, generate_master_key_str,bytes_to_b64str, b64str_to_bytes,
    KeyType, CryptoContextAES, CryptoContextMAC,
    AES_KEY_SIZE, SALT_SIZE, NONCE_SIZE, MAX_SECRET_LEN
)

# -----------------------------
# Helper Functions Tests
# -----------------------------
def test_hash_bytes():
    """Test hash_bytes function."""
    test_data = b"test data"
    result = hash_bytes(test_data)
    
    # Verify it's a base64 string
    assert isinstance(result, str)
    # Verify deterministic output
    assert hash_bytes(test_data) == result
    # Verify different input produces different hash
    assert hash_bytes(b"different") != result

# -----------------------------
# Key Generation Tests
# -----------------------------
def test_generate_salt_str():
    """Test salt generation."""
    salt = generate_salt_str()
    salt_bytes = b64str_to_bytes(salt)
    
    assert isinstance(salt, str)
    assert len(salt_bytes) == SALT_SIZE
    # Verify randomness
    assert generate_salt_str() != salt

def test_generate_master_key_str():
    """Test master key generation."""
    key = generate_master_key_str()
    key_bytes = b64str_to_bytes(key)
    
    assert isinstance(key, str)
    assert len(key_bytes) == AES_KEY_SIZE
    # Verify randomness
    assert generate_master_key_str() != key

# -----------------------------
# KeyType Tests
# -----------------------------
def test_key_type_definitions():
    """Test KeyType enum and definitions."""
    assert KeyType.AES.value.name == 'aes'
    assert KeyType.AES.value.alg == 'AESGCM'
    assert KeyType.AES.value.key_size == 32
    
    assert KeyType.MAC.value.name == 'mac'
    assert KeyType.MAC.value.alg == 'HMAC-SHA256'
    assert KeyType.MAC.value.key_size == 32

def test_key_derivation():
    """Test key derivation function."""
    master_key = os.urandom(32)
    salt = os.urandom(32)
    
    aes_key = KeyType.AES.value.derive_key(master_key, salt)
    mac_key = KeyType.MAC.value.derive_key(master_key, salt)
    
    assert len(aes_key) == AES_KEY_SIZE
    assert len(mac_key) == AES_KEY_SIZE
    assert aes_key != mac_key  # Different info parameters should produce different keys

# -----------------------------
# CryptoContextAES Tests
# -----------------------------
def test_aes_encrypt_decrypt():
    """Test AES encryption and decryption."""
    name = "test_secret"
    version = "v1"
    salt = os.urandom(SALT_SIZE)
    master_key = os.urandom(AES_KEY_SIZE)
    
    ctx = CryptoContextAES(name, version, salt, master_key)
    plaintext = "test secret value"
    
    # Test encryption
    nonce_b64, ct_b64 = ctx.encrypt(plaintext)
    assert isinstance(nonce_b64, str)
    assert isinstance(ct_b64, str)
    
    # Test decryption
    decrypted = ctx.decrypt(nonce_b64, ct_b64)
    assert decrypted == plaintext

def test_aes_authentication():
    """Test AES-GCM authentication."""
    ctx = CryptoContextAES("test", "v1", os.urandom(SALT_SIZE), os.urandom(AES_KEY_SIZE))
    nonce_b64, ct_b64 = ctx.encrypt("test")
    
    # Tamper with ciphertext
    ct_bytes = bytearray(b64str_to_bytes(ct_b64))
    ct_bytes[0] ^= 0xFF
    tampered_ct = bytes_to_b64str(bytes(ct_bytes))
    
    # Should fail authentication
    with pytest.raises(InvalidTag):
        ctx.decrypt(nonce_b64, tampered_ct)

def test_aes_max_length():
    """Test maximum plaintext length restriction."""
    ctx = CryptoContextAES("test", "v1", os.urandom(SALT_SIZE), os.urandom(AES_KEY_SIZE))
    too_long = "x" * (MAX_SECRET_LEN + 1)
    
    with pytest.raises(ValueError, match="value too large"):
        ctx.encrypt(too_long)

# -----------------------------
# CryptoContextMAC Tests
# -----------------------------

def test_mac_compute_verify():
    """Test MAC computation and verification."""
    salt = os.urandom(SALT_SIZE)
    master_key = os.urandom(AES_KEY_SIZE)
    ctx = CryptoContextMAC(salt, master_key)
    
    items = {
        "secret1": {"n": "nonce1", "ct": "ciphertext1"},
        "secret2": {"n": "nonce2", "ct": "ciphertext2"}
    }
    
    # Compute MAC
    mac = ctx.compute_items_mac(items)
    
    # Verify valid MAC
    ctx.verify_items_mac(items, mac)
    
    # Modify items and verify MAC fails
    items["secret1"]["ct"] = "tampered"
    with pytest.raises(InvalidSignature, match="Signature did not match digest"):
        ctx.verify_items_mac(items, mac)

def test_mac_canonicalization():
    """Test MAC canonicalization is deterministic."""
    ctx = CryptoContextMAC(os.urandom(SALT_SIZE), os.urandom(AES_KEY_SIZE))
    
    items1 = {"a": {"n": "1"}, "b": {"n": "2"}}
    items2 = {"b": {"n": "2"}, "a": {"n": "1"}}  # Different order
    
    mac1 = ctx.compute_items_mac(items1)
    mac2 = ctx.compute_items_mac(items2)
    
    assert mac1 == mac2  # Should produce same MAC regardless of order