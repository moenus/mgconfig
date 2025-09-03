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
def test_key_value_retrieves_from_keystore(mock_keystore):
    with patch.object(key_provider.KeyStores, "get", return_value=mock_keystore):
        key = key_provider.Key("store1", "item1")

        # First access triggers _retrieve_key
        val = key.value
        assert val == "secret_value"
        mock_keystore.get.assert_called_once_with("item1")

        # Second access uses cached value (get not called again)
        val2 = key.value
        assert val2 == "secret_value"
        mock_keystore.get.assert_called_once()  # still only 1 call


def test_key_value_set_saves_and_caches(mock_keystore):
    with patch.object(key_provider.KeyStores, "get", return_value=mock_keystore):
        key = key_provider.Key("store1", "item1")
        key.value = "new_secret"
        mock_keystore.set.assert_called_once_with("item1", "new_secret")
        assert key._item_value == "new_secret"
        assert str(key) == "new_secret"


def test_key_retrieve_key_raises_if_none(mock_keystore):
    mock_keystore.get.return_value = None
    with patch.object(key_provider.KeyStores, "get", return_value=mock_keystore):
        key = key_provider.Key("store1", "item1")
        with pytest.raises(ValueError, match="cannot provide a value"):
            _ = key.value

