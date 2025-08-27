import os
import json
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock

from mgconfig import keystores
from mgconfig.keystores import (
    KeyStore, KeyStoreFile, KeyStoreKeyring, KeyStoreEnv, KeyStores
)


# -----------------------------
# Base KeyStore
# -----------------------------
def test_keystore_set_raises():
    ks = KeyStore()
    with pytest.raises(ValueError):
        ks.set("foo", "bar")


def test_get_param_and_missing():
    ks = KeyStore()
    ks.params = {"foo": "bar"}
    assert ks.get_param("foo") == "bar"
    with pytest.raises(ValueError):
        ks.get_param("missing")


def test_check_configuration_unconfigured():
    ks = KeyStore()
    with pytest.raises(ValueError):
        ks.check_configuration()


@patch("mgconfig.keystores.config_values")
@patch("mgconfig.keystores.ConstConfig")
def test_configure_success(mock_const, mock_confvals):
    ks = KeyStore()
    ks.mandatory_conf_names = ["param1"]

    mock_const.return_value.config_id = "id1"
    mock_confvals.get.return_value.value = "val1"

    ks.configure()
    assert ks.params["param1"] == "val1"


@patch("mgconfig.keystores.config_values")
@patch("mgconfig.keystores.ConstConfig")
def test_configure_missing_value(mock_const, mock_confvals):
    ks = KeyStore()
    ks.mandatory_conf_names = ["param1"]

    mock_const.return_value.config_id = "id1"
    mock_confvals.get.return_value = None

    with pytest.raises(ValueError):
        ks.configure()


# -----------------------------
# KeyStoreFile
# -----------------------------
def test_filepath_reads_param():
    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.config_handle: "/tmp/test.json"}
    assert ks.filepath == "/tmp/test.json"


def test_check_configuration_loads_file(tmp_path):
    file = tmp_path / "data.json"
    file.write_text(json.dumps({"k1": "v1"}))

    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.config_handle: str(file)}

    ks.check_configuration()
    assert ks.filedata == {"k1": "v1"}


def test_check_configuration_empty_file_raises(tmp_path):
    file = tmp_path / "data.json"
    file.write_text("{}")

    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.config_handle: str(file)}
    with pytest.raises(ValueError):
        ks.check_configuration()


def test_get_and_set_roundtrip(tmp_path):
    file = tmp_path / "data.json"
    file.write_text(json.dumps({"a": "1"}))

    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.config_handle: str(file)}

    # load
    assert ks.get("a") == "1"

    # set new key
    ks.set("b", "2")
    assert ks.filedata["b"] == "2"
    assert json.loads(file.read_text())["b"] == "2"


def test_save_unwritable(monkeypatch, tmp_path):
    file = tmp_path / "data.json"
    file.write_text("{}")

    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.config_handle: str(file)}
    ks.filedata = {}

    # deny write
    monkeypatch.setattr("os.access", lambda *a, **kw: False)
    assert ks._save() is False


# -----------------------------
# KeyStoreKeyring
# -----------------------------
def test_service_name_reads_param():
    ks = KeyStoreKeyring()
    ks.params = {keystores.config_service_name.config_handle: "service"}
    assert ks.service_name == "service"


@patch("mgconfig.keystores.keyring.get_password", return_value="secret")
def test_keyring_get(mock_get):
    ks = KeyStoreKeyring()
    ks.params = {keystores.config_service_name.config_handle: "service"}
    assert ks.get("item") == "secret"
    mock_get.assert_called_once()


@patch("mgconfig.keystores.keyring.set_password")
def test_keyring_set(mock_set):
    ks = KeyStoreKeyring()
    ks.params = {keystores.config_service_name.config_handle: "service"}
    ks.set("item", "value")
    mock_set.assert_called_once_with("service", "item", "value")


# -----------------------------
# KeyStoreEnv
# -----------------------------
def test_env_get(monkeypatch):
    monkeypatch.setenv("MYVAR", "123")
    ks = KeyStoreEnv()
    assert ks.get("MYVAR") == "123"
    assert ks.get("MISSING") is None


# -----------------------------
# KeyStores registry
# -----------------------------
def test_add_and_get_contains():
    ks = KeyStore()
    ks.keystore_name = "custom"

    # Ensure fresh registry
    KeyStores._ks_dict = {}
    KeyStores.add(ks)

    assert KeyStores.contains("custom")
    assert KeyStores.get("custom") == ks

    with pytest.raises(ValueError):
        KeyStores.add(ks)
