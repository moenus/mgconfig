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


# ----------------------------
# Tests for get_from_conf
# ----------------------------
def test_get_from_conf_returns_value():
    fake_config_id = "SEC_master_key_item_name"
    fake_config_value = MagicMock()
    fake_config_value.value = "expected"

    with patch("mgconfig.key_provider.lazy_build_config_id", return_value=fake_config_id), \
         patch.object(key_provider, "config_values", {fake_config_id: fake_config_value}):
        val = key_provider.get_from_conf("master_key", "item_name")
        assert val == "expected"


def test_get_from_conf_missing_raises():
    fake_config_id = "SEC_master_key_item_name"
    with patch("mgconfig.key_provider.lazy_build_config_id", return_value=fake_config_id), \
         patch.object(key_provider, "config_values", {}):
        with pytest.raises(ValueError, match="Cannot find"):
            key_provider.get_from_conf("master_key", "item_name")


# ----------------------------
# Tests for KeyProvider
# ----------------------------
def test_keyprovider_initialization_and_get_set(mock_keystore):
    """Ensure KeyProvider loads config and can get/set values."""
    with patch("mgconfig.key_provider.get_from_conf", side_effect=["store1", "item1"]), \
         patch.object(key_provider.KeyStores, "contains", return_value=True), \
         patch.object(key_provider.KeyStores, "get", return_value=mock_keystore):

        provider = key_provider.KeyProvider()
        assert "master_key" in provider._keys

        # get() retrieves value from keystore
        val = provider.get("master_key")
        assert val == "secret_value"

        # set() updates both keystore and cache
        provider.set("master_key", "new_val")
        mock_keystore.set.assert_called_with("item1", "new_val")


def test_keyprovider_invalid_keystore_raises():
    with patch("mgconfig.key_provider.get_from_conf", return_value="invalid_store"), \
         patch.object(key_provider.KeyStores, "contains", return_value=False):
        with pytest.raises(ValueError, match="Invalid keystore name"):
            key_provider.KeyProvider()


def test_keyprovider_get_nonexistent_key_raises():
    with patch("mgconfig.key_provider.get_from_conf", side_effect=["store1", "item1"]), \
         patch.object(key_provider.KeyStores, "contains", return_value=True), \
         patch.object(key_provider.KeyStores, "get", return_value=MagicMock()):

        provider = key_provider.KeyProvider()
        with pytest.raises(KeyError, match="not found"):
            provider.get("other_key")


def test_keyprovider_set_nonexistent_key_raises():
    with patch("mgconfig.key_provider.get_from_conf", side_effect=["store1", "item1"]), \
         patch.object(key_provider.KeyStores, "contains", return_value=True), \
         patch.object(key_provider.KeyStores, "get", return_value=MagicMock()):

        provider = key_provider.KeyProvider()
        with pytest.raises(KeyError, match="not found"):
            provider.set("other_key", "value")
