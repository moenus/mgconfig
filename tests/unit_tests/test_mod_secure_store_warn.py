# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import json
import pytest
from mgconfig.secure_store import SecureStore, generate_key_str, bytes_to_b64str, b64str_to_bytes

class DummyKeyProvider:
    def __init__(self, master_key, salt):
        self._keys = {
            "master_key": master_key,
            "salt": salt
        }

    def get(self, name):
        return self._keys[name]


@pytest.fixture
def secure_store(tmp_path):
    master_key = generate_key_str()
    salt = generate_key_str()
    kp = DummyKeyProvider(master_key, salt)
    store_file = tmp_path / "secure.json"
    return SecureStore(str(store_file), kp)


@pytest.mark.parametrize("field", ["ciphertext", "nonce", "tag"])
def test_tampered_data_causes_decryption_failure_with_logging(secure_store, field, caplog):
    """Tampering with any encrypted field should make AES-GCM fail and log a warning."""
    secure_store.store_secret("secret", "supersecret")
    enc_entry = secure_store.securestore["secret"]

    # Tamper the chosen field
    tampered_bytes = bytearray(b64str_to_bytes(enc_entry[field]))
    tampered_bytes[0] ^= 0xFF
    enc_entry[field] = bytes_to_b64str(bytes(tampered_bytes))

    caplog.set_level("WARNING")
    result = secure_store.retrieve_secret("secret")

    assert result is None
    assert any("Decryption failed" in rec.message for rec in caplog.records)


def test_tampering_after_save_and_load_with_logging(secure_store, caplog):
    """Tampering after saving to disk should still fail and log a warning."""
    secure_store.store_secret("secret", "integritycheck")
    secure_store.save_securestore()

    # Load JSON and tamper with ciphertext
    with open(secure_store.securestore_file, "r") as f:
        data = json.load(f)
    tampered = bytearray(b64str_to_bytes(data["secret"]["ciphertext"]))
    tampered[0] ^= 0xAA
    data["secret"]["ciphertext"] = bytes_to_b64str(bytes(tampered))

    with open(secure_store.securestore_file, "w") as f:
        json.dump(data, f)

    caplog.set_level("WARNING")
    new_store = SecureStore(
        secure_store.securestore_file,
        DummyKeyProvider(secure_store.master_key_str, bytes_to_b64str(secure_store._salt))
    )
    result = new_store.retrieve_secret("secret")

    assert result is None
    assert any("Decryption failed" in rec.message for rec in caplog.records)
