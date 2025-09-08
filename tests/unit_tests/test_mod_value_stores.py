# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from typing import Any

from mgconfig import value_stores


# -----------------------------
# Fixtures / helpers
# -----------------------------

@pytest.fixture(autouse=True)
def reset_singletons():
    # Reset ValueStore singleton instances between tests
    value_stores.ValueStoreSecure.reset_instance()
    value_stores.ValueStoreFile.reset_instance()
    value_stores.ValueStoreEnv.reset_instance()
    value_stores.ValueStoreDefault.reset_instance()
    yield
    value_stores.ValueStoreSecure.reset_instance()
    value_stores.ValueStoreFile.reset_instance()
    value_stores.ValueStoreEnv.reset_instance()
    value_stores.ValueStoreDefault.reset_instance()


# -----------------------------
# ConfigValueSource Tests
# -----------------------------
def test_config_value_source_str():
    """Test string conversion of ConfigValueSource enum."""
    assert str(value_stores.ConfigValueSource.CFGFILE) == "cfgfile"
    assert str(value_stores.ConfigValueSource.ENV_VAR) == "env_var"
    assert str(value_stores.ConfigValueSource.DEFAULT) == "default"
    assert str(value_stores.ConfigValueSource.ENCRYPT) == "encrypt"


# -----------------------------
# ValueStore Base Class Tests
# -----------------------------
def test_valuestore_singleton():
    """Test ValueStore maintains singleton pattern."""
    class TestStore(value_stores.ValueStore):
        def save_value(self, item_id: str, value: Any) -> bool:
            return True

        def retrieve_value(self, item_id: str) -> tuple[Any, value_stores.ConfigValueSource]:
            return None, self._source

    store1 = TestStore(value_stores.ConfigValueSource.DEFAULT)
    store2 = TestStore(value_stores.ConfigValueSource.DEFAULT)
    assert store1 is store2

# -----------------------------
# ValueStoreFile
# -----------------------------


@patch("mgconfig.value_stores.config_items")
@patch("mgconfig.value_stores.ConfigDefs")
def test_file_retrieve_and_save(ConfigDefs, config_items, tmp_path):
    # Setup config file
    configfile = tmp_path / "config.yaml"
    configfile.write_text(yaml.dump({"section": {"key": "val"}}))

    # Mock config_items to return our test file path
    mock_config_value = MagicMock()
    mock_config_value.value = str(configfile)
    config_items.get_value.return_value = str(
        configfile)  # Changed from get to get_value

    # Setup ConfigDefs mock properly
    mock_cfg_defs = MagicMock()

    def fake_cfg_def_property(item_id, prop):
        if prop == str(value_stores.CDF.SECTION):
            return "section"
        elif prop == str(value_stores.CDF.NAME):
            return "key"
        return None
    mock_cfg_defs.cfg_def_property.side_effect = fake_cfg_def_property
    ConfigDefs.return_value = mock_cfg_defs

    # Test the store
    store = value_stores.ValueStoreFile()
    val, source = store.retrieve_value("dummy")

    assert val == "val"
    assert source == value_stores.ConfigValueSource.CFGFILE

    # Test save functionality
    assert store.save_value("dummy", "new_val") is True
    val, source = store.retrieve_value("dummy")
    assert val == "new_val"



@patch("mgconfig.value_stores.config_items")
def test_secure_store_initialization_logging(mock_items, caplog):
    """Test logging during secure store initialization."""
    # Set logging level to capture all messages
    caplog.set_level('DEBUG')
    
    # Setup mock config
    mock_config = MagicMock()
    mock_config.value = "test.sec"
    mock_items.get.return_value = mock_config

    with patch("mgconfig.value_stores.KeyProvider"):
        with patch("mgconfig.value_stores.SecureStore") as MockSecureStore:
            # Test successful initialization
            mock_store = MagicMock()
            mock_store.validate_master_key.return_value = True
            MockSecureStore.return_value = mock_store

            store = value_stores.ValueStoreSecure()
            assert "Secure store successfully initialized" in caplog.text

            # Test failed validation
            caplog.clear()
            mock_store.validate_master_key.return_value = False
            value_stores.ValueStoreSecure.reset_instance()  # Reset singleton
            store = value_stores.ValueStoreSecure()
            assert "Secure store corrupted or master key invalid." in caplog.text

def test_secure_store_save_logging(caplog):
    """Test logging during secure store save operations."""
    with patch("mgconfig.value_stores.config_items") as mock_items:
        mock_items.get.return_value = MagicMock(value="test.sec")

        with patch("mgconfig.value_stores.KeyProvider"):
            with patch("mgconfig.value_stores.SecureStore") as MockSecureStore:
                store = value_stores.ValueStoreSecure()

                # Test successful save
                caplog.clear()
                assert store.save_value("test_id", "secret")
                assert "saved to keystore" in caplog.text

                # Test failed save
                caplog.clear()
                MockSecureStore.return_value.store_secret.side_effect = Exception(
                    "Save failed")
                assert not store.save_value("test_id", "secret")
                assert "Cannot store secret" in caplog.text

# -----------------------------
# ValueStoreEnv
# -----------------------------


@patch("mgconfig.value_stores.ConfigDefs")
def test_env_retrieve(ConfigDefs, monkeypatch):
    ConfigDefs().cfg_def_property.return_value = "MY_ENV_VAR"
    monkeypatch.setenv("MY_ENV_VAR", "123")

    store = value_stores.ValueStoreEnv()
    val, source = store.retrieve_value("dummy")
    assert val == "123"
    assert source == value_stores.ConfigValueSource.ENV_VAR


def test_env_save_raises():
    store = value_stores.ValueStoreEnv()
    with pytest.raises(NotImplementedError):
        store.save_value("dummy", "val")


@patch("mgconfig.value_stores.ConfigDefs")
def test_env_retrieve_missing_env_var(ConfigDefs):
    """Test retrieving non-existent environment variable."""
    ConfigDefs().cfg_def_property.return_value = "NON_EXISTENT_VAR"

    store = value_stores.ValueStoreEnv()
    val, source = store.retrieve_value("dummy")
    assert val is None
    assert source == value_stores.ConfigValueSource.ENV_VAR


@patch("mgconfig.value_stores.ConfigDefs")
def test_env_retrieve_no_env_mapping(ConfigDefs):
    """Test retrieving when no environment variable is mapped."""
    ConfigDefs().cfg_def_property.return_value = None

    store = value_stores.ValueStoreEnv()
    val, source = store.retrieve_value("dummy")
    assert val is None
    assert source == value_stores.ConfigValueSource.ENV_VAR


# -----------------------------
# ValueStoreDefault
# -----------------------------

@patch("mgconfig.value_stores.ConfigDefs")
def test_default_retrieve_and_save(ConfigDefs):
    ConfigDefs().cfg_def_property.return_value = "defaultval"
    store = value_stores.ValueStoreDefault()

    val, source = store.retrieve_value("dummy")
    assert val == "defaultval"
    assert source == value_stores.ConfigValueSource.DEFAULT

    # save_value not supported
    with pytest.raises(NotImplementedError):
        store.save_value("dummy", "ignored")


# -----------------------------
# ValueStoreSecure
# -----------------------------

@patch("mgconfig.value_stores.KeyProvider")
@patch("mgconfig.value_stores.KeyProvider")
@patch("mgconfig.value_stores.config_items")
@patch("mgconfig.value_stores.SecureStore")
def test_secure_save_and_retrieve(SecureStore, config_items, KeyProvider, tmp_path):
    # Create a mock config value object
    mock_config_value = MagicMock()
    mock_config_value.value = str(tmp_path / "store.sec")
    config_items.get.return_value = mock_config_value

    # Rest of the test setup
    secure_mock = MagicMock()
    SecureStore.return_value = secure_mock
    secure_mock.validate_master_key.return_value = True
    secure_mock.retrieve_secret.return_value = "retrieved"
    secure_mock.prepare_auto_key_exchange.return_value = "newkey"

    store = value_stores.ValueStoreSecure()

    # save
    secure_mock.reset_mock()
    ok = store.save_value("item1", "secret")
    assert ok
    secure_mock.store_secret.assert_called_with("item1", "secret")
    secure_mock._ssf_save.assert_called()

    # retrieve
    val, source = store.retrieve_value("item1")
    assert val == "retrieved"
    assert source == value_stores.ConfigValueSource.ENCRYPT

    # new masterkey
    mk = store.prepare_new_masterkey()
    assert mk == "newkey"


@patch("mgconfig.value_stores.KeyProvider")
@patch("mgconfig.value_stores.config_items")
@patch("mgconfig.value_stores.ValueStoreSecure._get_new_secure_store")
def test_secure_error_cases(mock_get_store, mock_config_items, mock_KeyProvider, tmp_path):
    # Create a mock config value object
    mock_config_value = MagicMock()
    mock_config_value.value = str(tmp_path / "dummy.sec")
    mock_config_items.get.return_value = mock_config_value

    # KeyProvider just returns a dummy object
    mock_KeyProvider.return_value = object()

    # Simulate secure store raising errors
    mock_get_store.side_effect = Exception("boom")

    store = value_stores.ValueStoreSecure()

    ok = store.save_value("id", "secret")
    assert not ok

    val, source = store.retrieve_value("id")
    assert val is None
    assert source == value_stores.ConfigValueSource.ENCRYPT

    mk = store.prepare_new_masterkey()
    assert mk is None


# -----------------------------
# Utility function
# -----------------------------

@patch("mgconfig.value_stores.ValueStoreSecure")
def test_get_new_masterkey(MockVSS):
    mock_instance = MockVSS.return_value
    mock_instance.prepare_new_masterkey.return_value = "abc123"

    mk = value_stores.get_new_masterkey()
    assert mk == "abc123"

    MockVSS.assert_called_once()  # ensure constructor was used
    mock_instance.prepare_new_masterkey.assert_called_once()
