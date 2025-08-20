# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
from mgconfig.secure_store import (
    SecureStore,

    bytes_to_b64str,
    b64str_to_bytes,
    ITEMNAME_CIPHERTEXT,
    ITEMNAME_NONCE,
)
from mgconfig.secure_store_helpers import generate_key_str


class DummyKeyProvider:
    def __init__(self, master_key):
        self._keys = {
            "master_key": master_key,
        }

    def get(self, name):
        return self._keys[name]


@pytest.fixture
def secure_store(tmp_path):
    master_key = generate_key_str()
    kp = DummyKeyProvider(master_key)
    store_file = tmp_path / "secure.json"
    return SecureStore(str(store_file), kp)


def test_store_and_retrieve_secret(secure_store):
    secure_store.store_secret("foo", "bar")
    result = secure_store.retrieve_secret("foo")
    assert result == "bar"


def test_retrieve_nonexistent_secret(secure_store):
    assert secure_store.retrieve_secret("nope") is None


def test_store_and_retrieve_all_secrets(secure_store):
    secrets = {"a": "1", "b": "2"}
    for k, v in secrets.items():
        secure_store.store_secret(k, v)
    all_dec = secure_store.retrieve_all_secrets()
    for k in secrets:
        assert all_dec[k] == secrets[k]



# === CRYPTOGRAPHIC INTEGRITY TESTS ===

@pytest.mark.parametrize("field", ['n','ct'])
def test_tampered_data_causes_decryption_failure(secure_store, field):
    """Modifying any encrypted field should cause AES-GCM to fail authentication."""
    secure_store.store_secret("secret", "supersecret")
    enc_entry = secure_store._items["secret"]

    # Tamper with the chosen field
    tampered_bytes = bytearray(b64str_to_bytes(enc_entry[field]))
    tampered_bytes[0] ^= 0xFF  # flip bits in first byte
    enc_entry[field] = bytes_to_b64str(bytes(tampered_bytes))

    # Ensure decryption fails
    result = secure_store.retrieve_secret("secret")
    assert result is None


