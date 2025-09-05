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


# -----------------------------
# KeyStore Configuration Tests
# -----------------------------
def test_keystore_configure():
    """Test keystore configuration with valid parameters."""
    ks = KeyStore()
    ks.mandatory_confs = [keystores.config_keyfile]
    
    # Mock config_items
    mock_value = MagicMock()
    mock_value.value = "test_value"
    with patch('mgconfig.keystores.config_items.get', return_value=mock_value):
        ks.configure()
        assert ks.params[keystores.config_keyfile] == "test_value"

def test_keystore_configure_missing_value():
    """Test configuration fails with missing value."""
    ks = KeyStore()
    ks.mandatory_confs = [keystores.config_keyfile]
    
    # Mock config_items to return None
    with patch('mgconfig.keystores.config_items.get', return_value=None):
        with pytest.raises(ValueError, match="not found"):
            ks.configure()

# -----------------------------
# KeyStoreFile Tests
# -----------------------------
def test_keystore_file_filepath():
    """Test filepath property."""
    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.id: "/test/path"}
    assert ks.filepath == "/test/path"

def test_keystore_file_save_new_file(tmp_path):
    """Test saving to a new file."""
    filepath = tmp_path / "keys.json"
    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.id: str(filepath)}
    ks.filedata = {"test_key": "test_value"}
    
    assert ks._save() == True
    assert filepath.exists()
    with open(filepath) as f:
        saved_data = json.load(f)
        assert saved_data == {"test_key": "test_value"}

def test_keystore_file_save_error(tmp_path):
    """Test save handling write errors."""
    filepath = tmp_path / "keys.json"
    ks = KeyStoreFile()
    ks.params = {keystores.config_keyfile.id: str(filepath)}
    ks.filedata = {"test_key": "test_value"}
    
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = IOError("Test error")
        assert ks._save() == False

# -----------------------------
# KeyStoreKeyring Tests
# -----------------------------
@patch('keyring.get_password')
def test_keystore_keyring_get(mock_get):
    """Test keyring get operation."""
    mock_get.return_value = "test_value"
    ks = KeyStoreKeyring()
    ks.params = {keystores.config_service_name.id: "test_service"}
    
    assert ks.get("test_key") == "test_value"
    mock_get.assert_called_once_with("test_service", "test_key")

@patch('keyring.set_password')
def test_keystore_keyring_set(mock_set):
    """Test keyring set operation."""
    ks = KeyStoreKeyring()
    ks.params = {keystores.config_service_name.id: "test_service"}
    
    ks.set("test_key", "test_value")
    mock_set.assert_called_once_with("test_service", "test_key", "test_value")

def test_keystore_keyring_service_name():
    """Test service_name property."""
    ks = KeyStoreKeyring()
    ks.params = {keystores.config_service_name.id: "test_service"}
    assert ks.service_name == "test_service"

# -----------------------------
# Integration Tests
# -----------------------------
def test_keystores_initialization():
    """Test that default keystores are registered."""
    # Reset registry
    KeyStores._ks_dict = {}
    
    # Re-run initialization
    keystores.KeyStores.add(keystores.KeyStoreEnv())
    keystores.KeyStores.add(keystores.KeyStoreFile())
    keystores.KeyStores.add(keystores.KeyStoreKeyring())
    
    assert KeyStores.contains('env')
    assert KeyStores.contains('file')
    assert KeyStores.contains('keyring')
    
    assert isinstance(KeyStores.get('env'), KeyStoreEnv)
    assert isinstance(KeyStores.get('file'), KeyStoreFile)
    assert isinstance(KeyStores.get('keyring'), KeyStoreKeyring)