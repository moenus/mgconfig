# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import keyring

# Import the module under test
import mgconfig.keystores as keystores

KEYFILE_FILEPATH_ID = 'sec_keyfile_filepath'
KEYRING_SERVICE_NAME_ID = 'sec_keyring_service_name'

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for KeyStoreFile tests."""
    file_path = tmp_path / "keystore.json"
    file_path.write_text(json.dumps({"foo": "bar"}))
    return file_path


@pytest.fixture
def file_keystore(temp_json_file):
    ks = keystores.KeyStoreFile()
    ks.configure({KEYFILE_FILEPATH_ID: str(temp_json_file)})
    return ks


@pytest.fixture
def keyring_keystore():
    ks = keystores.KeyStoreKeyring()
    ks.configure({KEYRING_SERVICE_NAME_ID: "test_service"})
    return ks


def test_keystorefile_get_existing(file_keystore):
    assert file_keystore.get("foo") == "bar"


def test_keystorefile_get_non_existing(file_keystore):
    assert file_keystore.get("missing") is None


def test_keystorefile_set_and_get(tmp_path):
    file_path = tmp_path / "keystore.json"
    ks = keystores.KeyStoreFile()
    ks.configure({KEYFILE_FILEPATH_ID: str(file_path)})
    ks.filedata = {'newkey':'abc'}
    with open(file_path, "w") as f:
        json.dump(ks.filedata, f)
    ks.set("newkey", "newvalue")

    with open(file_path) as f:
        data = json.load(f)

    assert data["newkey"] == "newvalue"
    assert ks.get("newkey") == "newvalue"


def test_keystorefile_save_permission_denied(tmp_path):
    file_path = tmp_path / "keystore.json"
    file_path.write_text("{}")  # make sure file exists
    ks = keystores.KeyStoreFile()
    ks.configure({KEYFILE_FILEPATH_ID: str(file_path)})
    ks.filedata = {"test": "value"}

    with patch("os.access", return_value=False):
        assert ks._save() is False


def test_keystorefile_invalid_json(tmp_path):
    file_path = tmp_path / "keystore.json"
    file_path.write_text("{invalid_json")
    ks = keystores.KeyStoreFile()
    ks.configure({KEYFILE_FILEPATH_ID: str(file_path)})

    with pytest.raises(json.JSONDecodeError):
        ks.check_configuration()


def test_keyringkeystore_get_set(keyring_keystore):
    with patch.object(keyring, "set_password") as mock_set, \
            patch.object(keyring, "get_password", return_value="secret") as mock_get:

        keyring_keystore.set("username", "secret")
        mock_set.assert_called_once_with("test_service", "username", "secret")

        value = keyring_keystore.get("username")
        mock_get.assert_called_once_with("test_service", "username")
        assert value == "secret"


def test_keystoreenv_get(monkeypatch):
    ks = keystores.KeyStoreEnv()
    monkeypatch.setenv("MY_ENV_VAR", "env_value")
    assert ks.get("MY_ENV_VAR") == "env_value"
    monkeypatch.delenv("MY_ENV_VAR", raising=False)
    assert ks.get("MY_ENV_VAR") is None


def test_keystores_registry():
    ks_env = keystores.KeyStoreEnv()
    keystores.KeyStores._ks_dict.clear()
    keystores.KeyStores.add(ks_env)
    assert keystores.KeyStores.contains("env")
    assert keystores.KeyStores.get("env") is ks_env

    with pytest.raises(ValueError):
        keystores.KeyStores.add(ks_env)  # duplicate


def test_configure_missing_param():
    ks = keystores.KeyStoreFile()
    with pytest.raises(ValueError):
        ks.configure({"wrong_param": "value"})


def test_get_param_missing():
    ks = keystores.KeyStoreFile()
    ks.params = {}
    with pytest.raises(ValueError):
        ks.get_param("missing")


def test_check_configuration_not_configured():
    ks = keystores.KeyStoreEnv()
    with pytest.raises(ValueError):
        ks.check_configuration()
