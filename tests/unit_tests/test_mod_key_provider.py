# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import patch, MagicMock

from mgconfig import key_provider


@pytest.fixture
def mock_keystore():
    """Fixture to create a mocked keystore with get/set/configure."""
    keystore = MagicMock()
    keystore.get.return_value = "secret_value"
    keystore.set = MagicMock()
    keystore.configure = MagicMock()
    return keystore


# ----------------------------
# Tests for Key
# ----------------------------
@patch('mgconfig.key_provider.KeyStores')
def test_key_value_retrieves_from_keystore(MockKeyStores):
    """Test that key value is retrieved from keystore."""
    # Setup mock keystore and value
    mock_keystore = MagicMock()
    mock_keystore.get.return_value = "test_value"

    # Setup KeyStores class mock
    MockKeyStores.get.return_value = mock_keystore
    MockKeyStores.get_key.return_value = "test_value"

    # Create and test key
    key = key_provider.Key("store1", "item1")
    assert key.value == "test_value"

    # Verify correct interaction with KeyStores
    MockKeyStores.get_key.assert_called_once_with("store1", "item1")


@patch('mgconfig.key_provider.KeyStores')
def test_key_value_set_saves_and_caches(MockKeyStores):
    """Test that setting a key value saves to keystore and updates cache."""
    # Setup mock keystore
    mock_keystore = MagicMock()
    mock_keystore.set.return_value = True

    # Setup KeyStores class mock
    MockKeyStores.get.return_value = mock_keystore
    MockKeyStores.prepare_params.return_value = None
    MockKeyStores.set_key.return_value = True
    MockKeyStores.get_key.return_value = "new_value"

    # Create key and set value
    key = key_provider.Key("store1", "item1")
    key.value = "new_value"

    # Verify interactions
    MockKeyStores.set_key.assert_called_once_with(
        "store1", "item1", "new_value")
    assert key.value == "new_value"  # Verify cached value

    # Verify second retrieval doesn't hit keystore
    MockKeyStores.get_key.reset_mock()
    cached_value = key.value
    assert cached_value == "new_value"
    MockKeyStores.get_key.assert_not_called()


@patch('mgconfig.key_provider.KeyStores')
def test_key_retrieve_key_raises_if_none(MockKeyStores):
    """Test that retrieving a non-existent key raises ValueError."""
    # Setup KeyStores mock
    mock_keystore = MagicMock()
    mock_keystore.get.return_value = None
    
    # Setup KeyStores class mock
    MockKeyStores.get.return_value = mock_keystore
    MockKeyStores.get_key.return_value = None
    
    # Create key and test value retrieval
    key = key_provider.Key("store1", "item1")
    
    expected_error = "Keystore store1 cannot provide a value for item1"
    with pytest.raises(ValueError, match=expected_error):
        _ = key.value
    
    # Verify interactions
    MockKeyStores.get_key.assert_called_once_with("store1", "item1")
