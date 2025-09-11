# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import json
import keyring
import os

from mgconfig.keystore_classes import (
    KeyStore, KeyStoreFile, KeyStoreKeyring, KeyStoreEnv,
    config_keyfile, config_service_name
)

# -----------------------------
# Fixtures
# -----------------------------


@pytest.fixture
def mock_config_items():
    """Provide mock config items."""
    with patch('mgconfig.keystore_classes.config_items') as mock:
        mock_value = MagicMock()
        mock_value.value = "test_value"
        mock.get.return_value = mock_value
        yield mock

# -----------------------------
# KeyStore Base Class Tests
# -----------------------------


def test_keystore_initialization():
    """Test KeyStore base class initialization."""
    ks = KeyStore()
    assert ks.params == {}
    assert ks.keystore_name == "unknown"
    assert isinstance(ks.mandatory_config_items, list)


def test_keystore_prepare_params(mock_config_items):
    """Test KeyStore parameter preparation."""
    ks = KeyStore()
    ks.mandatory_config_items = [config_keyfile]

    ks.prepare_params()
    assert ks.params[config_keyfile.id] == "test_value"


def test_keystore_missing_mandatory_raises():
    """Test that missing mandatory config raises ValueError."""
    ks = KeyStore()
    ks.mandatory_config_items = [config_keyfile]

    with patch('mgconfig.keystore_classes.config_items') as mock:
        mock.get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            ks.prepare_params()


def test_keystore_check_configuration():
    """Test configuration check."""
    ks = KeyStore()
    with pytest.raises(ValueError, match="not configured properly"):
        ks.check_configuration()

    ks.params["test"] = "value"
    ks.check_configuration()  # Should not raise

# -----------------------------
# KeyStoreFile Tests
# -----------------------------


def test_keystore_file_operations(tmp_path):
    """Test KeyStoreFile read/write operations."""
    file_path = tmp_path / "test_keys.json"

    # Setup keystore
    ks = KeyStoreFile()
    ks.params[config_keyfile.id] = str(file_path)

    # Test write
    ks.set("test_key", "test_value")
    assert file_path.exists()

    # Test read
    assert ks.get("test_key") == "test_value"

    # Test missing key
    assert ks.get("missing_key") is None


# -----------------------------
# KeyStoreKeyring Tests
# -----------------------------


def test_keystore_keyring_get():
    """Test KeyStoreKeyring get operation."""
    ks = KeyStoreKeyring()
    ks.params[config_service_name.id] = "test_service"

    with patch('keyring.get_password', return_value="test_value"):
        assert ks.get("test_key") == "test_value"


def test_keystore_keyring_set():
    """Test KeyStoreKeyring set operation."""
    ks = KeyStoreKeyring()
    ks.params[config_service_name.id] = "test_service"

    with patch('keyring.set_password') as mock_set:
        ks.set("test_key", "test_value")
        mock_set.assert_called_once_with(
            "test_service", "test_key", "test_value")


def test_keystore_keyring_error_handling():
    """Test KeyStoreKeyring error handling."""
    ks = KeyStoreKeyring()
    ks.params[config_service_name.id] = "test_service"

    with patch('keyring.get_password', side_effect=Exception("Test error")):
        with pytest.raises(KeyError, match="Cannot read from keyring"):
            ks.get("test_key")

# -----------------------------
# KeyStoreEnv Tests
# -----------------------------


def test_keystore_env_get(monkeypatch):
    """Test KeyStoreEnv get operation."""
    monkeypatch.setenv("TEST_KEY", "test_value")

    ks = KeyStoreEnv()
    assert ks.get("TEST_KEY") == "test_value"
    assert ks.get("MISSING_KEY") is None


def test_keystore_env_set():
    """Test KeyStoreEnv set operation (should raise ValueError)."""
    ks = KeyStoreEnv()
    with pytest.raises(ValueError, match="Cannot update keys"):
        ks.set("TEST_KEY", "test_value")
