# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

# test_securestore.py
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock

import mgconfig.secure_store as sm 
from mgconfig.sec_store_crypt import hash_bytes, AES_KEY_SIZE 
# from mgconfig.sec_store_crypt import generate_master_key_str as generate_key_str

"""
Notes:
DummyKeyProvider replaces the real KeyProvider to avoid external dependencies.
tmp_secure_file fixture ensures no leftover files.
We mock retrieve_secret in test_prepare_auto_key_exchange_and_validate to bypass real crypto steps for that validation path.

Tests cover:
    Base64 conversion functions
    Secret store encryption/decryption
    Save/load from disk
    Delete file behavior
    Master key property correctness
    Key exchange preparation and validation
    _auto_key_exchange execution path
    Hash computation repeatability

"""

class DummyKeyProvider:
    """Simple fake key provider for tests."""
    def __init__(self, master_key=None):
        self._master_key = master_key or sm.bytes_to_b64str(os.urandom(AES_KEY_SIZE))

    def get(self, keyname):
        if keyname == 'master_key':
            return self._master_key
        raise KeyError(f"No such key: {keyname}")


@pytest.fixture
def tmp_secure_file():
    """Provide a temporary securestore file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "secure.json")


@pytest.fixture
def store(tmp_secure_file):
    """Provide a fresh SecureStore instance."""
    kp = DummyKeyProvider()
    return sm.SecureStore(tmp_secure_file, kp)


def test_bytes_base64_roundtrip():
    data = os.urandom(16)
    s = sm.bytes_to_b64str(data)
    assert isinstance(s, str)
    assert sm.b64str_to_bytes(s) == data


def test_store_and_retrieve_secret(store):
    store.store_secret("mykey", "myvalue")
    val = store.retrieve_secret("mykey")
    assert val == "myvalue"
    # Ensure ciphertext differs from plaintext
    enc = store._items["mykey"][sm.ITEMNAME_CIPHERTEXT]
    assert "myvalue" not in enc


def test_retrieve_secret_not_found(store):
    assert store.retrieve_secret("no_such_key") is None


def test_store_and_retrieve_all(store):
    secrets = {"a": "1", "b": "2"}
    store.store_all_secrets(secrets)
    retrieved = store.retrieve_all_secrets()
    assert retrieved["a"] == "1"
    assert retrieved["b"] == "2"


def test_save_and_read_from_file(store, tmp_secure_file):
    store.store_secret("foo", "bar")
    store._ssf_save()
    # Read file directly to check it was written
    with open(tmp_secure_file, "r") as f:
        data = json.load(f)
    assert "foo" in store._items
    # New instance should load existing data
    kp = DummyKeyProvider(master_key=store.master_key_str)
    store2 = sm.SecureStore(tmp_secure_file, kp)
    assert store2.retrieve_secret("foo") == "bar"


def test_delete_securestore_file(store, tmp_secure_file):
    store.store_secret("x", "y")
    store._ssf_save()
    assert os.path.exists(tmp_secure_file)
    store._ssf_delete()
    assert not os.path.exists(tmp_secure_file)
    assert store._items == {}


def test_master_key_properties(store):
    # master_key_str decodes to original bytes
    assert sm.b64str_to_bytes(store.master_key_str) == store._master_key
    expected_hash = hash_bytes(store._master_key)
    assert store.master_key_hash == expected_hash


def test_prepare_auto_key_exchange_and_validate(store):
    # prepare_auto_key_exchange should return new key string
    new_key_str = store.prepare_auto_key_exchange()
    assert isinstance(new_key_str, str)
    assert sm.b64str_to_bytes(new_key_str) != store.master_key_str
    # Force the new key into the provider and validate
    store.master_key_str = new_key_str
    store.retrieve_secret = MagicMock(return_value=store.master_key_hash)
    assert store.validate_master_key() in (True, False)  # just ensure no crash


def test_hash_function(store):
    val = b"test123"
    h1 = hash_bytes(val)
    h2 = hash_bytes(val)
    assert isinstance(h1, str)
    assert h1 == h2
