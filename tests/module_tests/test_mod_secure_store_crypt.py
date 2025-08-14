import os
import json
import pytest
from mgconfig.secure_store import (
    SecureStore,
    generate_key_str,
    bytes_to_b64str,
    b64str_to_bytes,
    ITEMNAME_CIPHERTEXT,
    ITEMNAME_NONCE,
    ITEMNAME_TAG
)


class DummyKeyProvider:
    def __init__(self, master_key, salt_key):
        self._keys = {
            "master_key": master_key,
            "salt_key": salt_key
        }

    def get(self, name):
        return self._keys[name]


@pytest.fixture
def secure_store(tmp_path):
    master_key = generate_key_str()
    salt_key = generate_key_str()
    kp = DummyKeyProvider(master_key, salt_key)
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


def test_delete_securestore_file(secure_store):
    secure_store.store_secret("foo", "bar")
    secure_store.save_securestore()
    assert os.path.exists(secure_store.securestore_file)
    secure_store.delete_securestore_file()
    assert not os.path.exists(secure_store.securestore_file)
    assert secure_store.securestore == {}


def test_save_and_reload(secure_store):
    secure_store.store_secret("foo", "bar")
    secure_store.save_securestore()
    # reload
    new_store = SecureStore(secure_store.securestore_file,
                            DummyKeyProvider(
                                secure_store.master_key_str,
                                bytes_to_b64str(secure_store._salt_key)
                            ))
    assert new_store.retrieve_secret("foo") == "bar"


# === CRYPTOGRAPHIC INTEGRITY TESTS ===

@pytest.mark.parametrize("field", [ITEMNAME_CIPHERTEXT, ITEMNAME_NONCE, ITEMNAME_TAG])
def test_tampered_data_causes_decryption_failure(secure_store, field):
    """Modifying any encrypted field should cause AES-GCM to fail authentication."""
    secure_store.store_secret("secret", "supersecret")
    enc_entry = secure_store.securestore["secret"]

    # Tamper with the chosen field
    tampered_bytes = bytearray(b64str_to_bytes(enc_entry[field]))
    tampered_bytes[0] ^= 0xFF  # flip bits in first byte
    enc_entry[field] = bytes_to_b64str(bytes(tampered_bytes))

    # Ensure decryption fails
    result = secure_store.retrieve_secret("secret")
    assert result is None


def test_tampering_detected_even_after_save_and_load(secure_store):
    """Tampering after save and reload should still fail."""
    secure_store.store_secret("secret", "integritycheck")
    secure_store.save_securestore()

    # Load JSON and tamper with ciphertext
    with open(secure_store.securestore_file, "r") as f:
        data = json.load(f)
    entry = data["secret"]
    tampered = bytearray(b64str_to_bytes(entry[ITEMNAME_CIPHERTEXT]))
    tampered[0] ^= 0xAA
    entry[ITEMNAME_CIPHERTEXT] = bytes_to_b64str(bytes(tampered))

    with open(secure_store.securestore_file, "w") as f:
        json.dump(data, f)

    # Reload store and test
    new_store = SecureStore(
        secure_store.securestore_file,
        DummyKeyProvider(secure_store.master_key_str, bytes_to_b64str(secure_store._salt_key))
    )
    assert new_store.retrieve_secret("secret") is None
