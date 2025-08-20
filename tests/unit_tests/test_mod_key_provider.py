import pytest
from unittest.mock import MagicMock, patch
from mgconfig.key_provider import Key, KeyProvider, get_from_conf, MASTERKEYNAME


# --- Tests for Key class ---
def test_key_value_retrieval_and_cache():
    mock_keystore = MagicMock()
    mock_keystore.get.return_value = "secret_value"

    with patch("mgconfig.key_provider.KeyStores.get", return_value=mock_keystore):
        key = Key("teststore", "testitem")
        # Value should be retrieved from keystore
        assert key.value == "secret_value"
        # Cached value should be used on second access
        mock_keystore.get.assert_called_once()
        assert key.value == "secret_value"


def test_key_value_setter_updates_keystore_and_cache():
    mock_keystore = MagicMock()
    with patch("mgconfig.key_provider.KeyStores.get", return_value=mock_keystore):
        key = Key("teststore", "testitem")
        key.value = "new_value"
        mock_keystore.set.assert_called_once_with("testitem", "new_value")
        assert key._item_value == "new_value"


def test_key_retrieve_raises_when_value_missing():
    mock_keystore = MagicMock()
    mock_keystore.get.return_value = None
    with patch("mgconfig.key_provider.KeyStores.get", return_value=mock_keystore):
        key = Key("teststore", "missing_item")
        with pytest.raises(ValueError):
            _ = key.value


# --- Tests for get_from_conf ---
def test_get_from_conf_returns_value():
    conf = {"sec_test_key_item_name": "value123"}
    with patch("mgconfig.key_provider.lazy_build_config_id", return_value="sec_test_key_item_name"):
        assert get_from_conf(conf, "test_key", "item_name") == "value123"


def test_get_from_conf_raises_if_missing():
    conf = {}
    with patch("mgconfig.key_provider.lazy_build_config_id", return_value="sec_missing_item"):
        with pytest.raises(ValueError):
            get_from_conf(conf, "missing_key", "item_name")


# --- Tests for KeyProvider ---
def test_keyprovider_initialization_and_get(monkeypatch):
    mock_keystore = MagicMock()
    mock_keystore.get.return_value = "mock_value"
    mock_keystore.configure = MagicMock()
    
    # Patch KeyStores methods
    monkeypatch.setattr("mgconfig.key_provider.KeyStores.get", lambda name: mock_keystore)
    monkeypatch.setattr("mgconfig.key_provider.KeyStores.contains", lambda name: True)

    # Configuration mock
    conf = {
        "sec_salt_keystore": "ks1",
        "sec_salt_item_name": "salt_item",
        "sec_master_key_keystore": "ks1",
        "sec_master_key_item_name": "master_item"
    }

    with patch("mgconfig.key_provider.get_from_conf", side_effect=lambda c, k, v: conf[f"sec_{k}_{v}"]):
        provider = KeyProvider(conf)
        # Test getting a key value
        assert provider.get(MASTERKEYNAME) == "mock_value"


def test_keyprovider_get_set_raises_for_invalid_key(monkeypatch):
    mock_keystore = MagicMock()
    monkeypatch.setattr("mgconfig.key_provider.KeyStores.get", lambda name: mock_keystore)
    monkeypatch.setattr("mgconfig.key_provider.KeyStores.contains", lambda name: True)
    conf = {
        "sec_salt_keystore": "ks1",
        "sec_salt_item_name": "salt_item",
        "sec_master_key_keystore": "ks1",
        "sec_master_key_item_name": "master_item"
    }

    with patch("mgconfig.key_provider.get_from_conf", side_effect=lambda c, k, v: conf[f"sec_{k}_{v}"]):
        provider = KeyProvider(conf)
        with pytest.raises(KeyError):
            provider.get("invalid_key")
        with pytest.raises(KeyError):
            provider.set("invalid_key", "value")
