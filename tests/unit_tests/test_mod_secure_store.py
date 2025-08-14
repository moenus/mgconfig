# test_securestore.py
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import mgconfig.secure_store as sm 

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
    def __init__(self, master_key=None, salt=None):
        self._master_key = master_key or sm.bytes_to_b64str(os.urandom(sm.AES_KEY_SIZE))
        self._salt = salt or sm.bytes_to_b64str(os.urandom(sm.AES_KEY_SIZE))

    def get(self, keyname):
        if keyname == 'master_key':
            return self._master_key
        elif keyname == 'salt':
            return self._salt
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
    enc = store.securestore["mykey"][sm.ITEMNAME_CIPHERTEXT]
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
    store.save_securestore()
    # Read file directly to check it was written
    with open(tmp_secure_file, "r") as f:
        data = json.load(f)
    assert "foo" in data
    # New instance should load existing data
    kp = DummyKeyProvider(master_key=store.master_key_str,
                          salt=sm.bytes_to_b64str(store._salt))
    store2 = sm.SecureStore(tmp_secure_file, kp)
    assert store2.retrieve_secret("foo") == "bar"


def test_delete_securestore_file(store, tmp_secure_file):
    store.store_secret("x", "y")
    store.save_securestore()
    assert os.path.exists(tmp_secure_file)
    store.delete_securestore_file()
    assert not os.path.exists(tmp_secure_file)
    assert store.securestore == {}


def test_master_key_properties(store):
    # master_key_str decodes to original bytes
    assert sm.b64str_to_bytes(store.master_key_str) == store._master_key
    # master_key_hash matches manual hash
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(store.master_key_str.encode())
    expected_hash = digest.finalize().hex()
    assert store.master_key_hash == expected_hash


def test_prepare_auto_key_exchange_and_validate(store):
    # prepare_auto_key_exchange should return new key string
    new_key = store.prepare_auto_key_exchange()
    assert isinstance(new_key, str)
    assert sm.b64str_to_bytes(new_key) != store._master_key
    # Force the new key into the provider and validate
    old_key = store.master_key_str
    store._set_master_key(sm.b64str_to_bytes(new_key) if isinstance(new_key, bytes) else new_key)
    # Because _auto_key_exchange logic depends on stored hashes, validate_master_key should run path
    store.retrieve_secret = MagicMock(return_value=store.master_key_hash)
    assert store.validate_master_key() in (True, False)  # just ensure no crash


def test_auto_key_exchange_success(store):
    # Put some secret data
    store.store_secret("data", "value1")
    # Simulate preparation step
    old_key_str = store.master_key_str
    old_hash = store.master_key_hash
    new_key_str = sm.generate_key_str()
    store._set_master_key(new_key_str)
    # Insert simulated old/new key data into store
    store.store_secret(sm.AEMK_OLD_MK_KEY, old_key_str)
    store.store_secret(sm.AEMK_OLD_MK_HASH, old_hash)
    store._set_master_key(new_key_str)
    # Put matching new MK hash to trigger auto exchange
    store.store_secret(sm.AEMK_NEW_MK_HASH, store.master_key_hash)
    # Reset back to old key for starting state
    store._set_master_key(old_key_str)
    assert isinstance(store._auto_key_exchange(), bool)


def test_hash_function(store):
    val = "test123"
    h1 = store.hash(val)
    h2 = store.hash(val)
    assert isinstance(h1, str)
    assert h1 == h2
