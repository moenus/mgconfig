# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


import pytest
from unittest.mock import patch, mock_open, MagicMock

from mgconfig.keystores import (
    KeyStore, KeyStoreFile, KeyStoreKeyring, KeyStoreEnv, KeyStores
)


# -----------------------------
# KeyStores Registry Tests
# -----------------------------
@pytest.fixture(autouse=True)
def clear_registry():
    """Clear KeyStores registry before and after each test."""
    KeyStores._ks_dict = {}
    yield
    KeyStores._ks_dict = {}

def test_keystore_add_and_contains():
    """Test adding keystores and checking existence."""
    ks = KeyStore()
    ks.keystore_name = "test_store"
    
    KeyStores.add(ks)
    assert KeyStores.contains("test_store")
    assert not KeyStores.contains("nonexistent")

def test_keystore_add_duplicate_raises():
    """Test that adding duplicate keystore raises ValueError."""
    ks1 = KeyStore()
    ks1.keystore_name = "test_store"
    KeyStores.add(ks1)
    
    ks2 = KeyStore()
    ks2.keystore_name = "test_store"
    with pytest.raises(ValueError, match="already existing"):
        KeyStores.add(ks2)

def test_keystore_get():
    """Test retrieving keystores."""
    ks = KeyStore()
    ks.keystore_name = "test_store"
    KeyStores.add(ks)
    
    assert KeyStores.get("test_store") is ks
    with pytest.raises(ValueError, match="Invalid keystore"):
        KeyStores.get("nonexistent")

def test_keystore_get_key():
    """Test retrieving keys from keystores."""
    # Setup mock keystore
    mock_store = MagicMock(spec=KeyStore)
    mock_store.keystore_name = "mock_store"
    mock_store.get.return_value = "test_value"
    KeyStores.add(mock_store)
    
    assert KeyStores.get_key("mock_store", "test_key") == "test_value"
    mock_store.get.assert_called_once_with("test_key")
    
    with pytest.raises(ValueError, match="Invalid keystore"):
        KeyStores.get_key("nonexistent", "test_key")

def test_keystore_set_key():
    """Test setting keys in keystores."""
    # Setup mock keystore
    mock_store = MagicMock(spec=KeyStore)
    mock_store.keystore_name = "mock_store"
    KeyStores.add(mock_store)
    
    KeyStores.set_key("mock_store", "test_key", "test_value")
    mock_store.set.assert_called_once_with("test_key", "test_value")
    
    with pytest.raises(ValueError, match="Invalid keystore"):
        KeyStores.set_key("nonexistent", "test_key", "test_value")

def test_keystore_check_keystore():
    """Test keystore validation."""
    ks = KeyStore()
    ks.keystore_name = "test_store"
    KeyStores.add(ks)
    
    # Should not raise for existing store
    KeyStores.check_keystore("test_store")
    
    # Should raise for non-existent store
    with pytest.raises(ValueError, match="Invalid keystore"):
        KeyStores.check_keystore("nonexistent")

def test_keystore_list_keystores():
    """Test listing registered keystores."""
    # Add multiple keystores
    stores = ["store1", "store2", "store3"]
    for name in stores:
        ks = KeyStore()
        ks.keystore_name = name
        KeyStores.add(ks)
    
    keystore_list = KeyStores.list_keystores()
    assert isinstance(keystore_list, list)
    assert len(keystore_list) == len(stores)
    for name in stores:
        assert name in keystore_list

def test_default_keystores():
    """Test default keystore initialization."""
    # Clear registry and re-add default keystores
    KeyStores._ks_dict = {}
    KeyStores.add(KeyStoreEnv())
    KeyStores.add(KeyStoreFile())
    KeyStores.add(KeyStoreKeyring())
    
    # Verify default keystores
    assert KeyStores.contains("env")
    assert isinstance(KeyStores.get("env"), KeyStoreEnv)
    
    assert KeyStores.contains("file")
    assert isinstance(KeyStores.get("file"), KeyStoreFile)
    
    assert KeyStores.contains("keyring")
    assert isinstance(KeyStores.get("keyring"), KeyStoreKeyring)