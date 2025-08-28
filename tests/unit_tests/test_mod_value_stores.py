import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock

from  mgconfig import value_stores


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
# ValueStoreFile
# -----------------------------

@patch("mgconfig.value_stores.config_values")
@patch("mgconfig.value_stores.ConfigDefs")
def test_file_retrieve_and_save(ConfigDefs, config_values, tmp_path):
    # Setup config file
    configfile = tmp_path / "config.yaml"
    configfile.write_text(yaml.dump({"section": {"key": "val"}}))

    # Mock config_values to return our test file path
    mock_config_value = MagicMock()
    mock_config_value.value = str(configfile)
    config_values.get.return_value = mock_config_value

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



@patch("mgconfig.value_stores.config_values")
def test_file_missing_file_returns_empty(config_values, tmp_path):
    config_values.get.return_value.value = str(tmp_path / "nofile.yaml")
    store = value_stores.ValueStoreFile()
    assert store.configfile_content == {}


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
@patch("mgconfig.value_stores.config_values")
@patch("mgconfig.value_stores.SecureStore")
def test_secure_save_and_retrieve(SecureStore, config_values, KeyProvider, tmp_path):
    # Create a mock config value object
    mock_config_value = MagicMock()
    mock_config_value.value = str(tmp_path / "store.sec")
    config_values.get.return_value = mock_config_value

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
@patch("mgconfig.value_stores.config_values")
@patch("mgconfig.value_stores.ValueStoreSecure._get_new_secure_store")
def test_secure_error_cases(mock_get_store, mock_config_values, mock_KeyProvider, tmp_path):
    # Create a mock config value object
    mock_config_value = MagicMock()
    mock_config_value.value = str(tmp_path / "dummy.sec")
    mock_config_values.get.return_value = mock_config_value

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
