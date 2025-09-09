# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import json
import pytest
from mgconfig.secure_store import SecureStore
from mgconfig.sec_store_crypt import generate_master_key_str, bytes_to_b64str, b64str_to_bytes

class DummyKeyProvider:
    def __init__(self, master_key):
        self._keys = {
            "master_key": master_key,
        }

    def get(self, name):
        return self._keys[name]


@pytest.fixture
def secure_store(tmp_path):
    master_key = generate_master_key_str()
    kp = DummyKeyProvider(master_key)
    store_file = tmp_path / "secure.json"
    return SecureStore(str(store_file), kp)


@pytest.mark.parametrize("field", ['n','ct'])
def test_tampered_data_causes_decryption_failure_with_logging(secure_store, field, caplog):
    """Tampering with any encrypted field should make AES-GCM fail and log a warning."""
    secure_store.store_secret("secret", "supersecret")
    enc_entry = secure_store._items["secret"]

    # Tamper the chosen field
    tampered_bytes = bytearray(b64str_to_bytes(enc_entry[field]))
    tampered_bytes[0] ^= 0xFF
    enc_entry[field] = bytes_to_b64str(bytes(tampered_bytes))

    caplog.set_level("WARNING")
    result = secure_store.retrieve_secret("secret")

    assert result is None
    assert any("Decryption failed" in rec.message for rec in caplog.records)


