import os
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import mgconfig.value_stores as vs 


@pytest.fixture
def cfg_defs():
    """Fake ConfigDefs that behaves like a dict with .get()."""
    return {
        "item1": {str(vs.CDF.SECTION): "section1", str(vs.CDF.NAME): "key1", str(vs.CDF.ENV): "ENV_VAR1", str(vs.CDF.DEFAULT): "default1"},
        "item2": {str(vs.CDF.SECTION): "section2", str(vs.CDF.NAME): "key2"},
    }


# -------------------- ValueStoreFile --------------------

def test_file_store_read_and_write(tmp_path, cfg_defs):
    config_path = tmp_path / "config.yml"
    init_config = {vs.config_configfile.config_id: str(config_path)}

    store = vs.ValueStoreFile(cfg_defs, init_config)

    # Initially empty
    assert store.retrieve_value("item1") == (None, vs.ConfigValueSource.CFGFILE)

    # Save and check file contents
    assert store.save_value("item1", "myvalue") is True
    with open(config_path) as f:
        data = yaml.safe_load(f)
    assert data["section1"]["key1"] == "myvalue"

    # Retrieval works
    val, src = store.retrieve_value("item1")
    assert val == "myvalue"
    assert src == vs.ConfigValueSource.CFGFILE


def test_file_store_missing_file(tmp_path, cfg_defs):
    init_config = {vs.config_configfile.config_id: str(tmp_path / "doesnotexist.yml")}
    store = vs.ValueStoreFile(cfg_defs, init_config)
    assert store.configfile_content == {}


def test_file_store_write_failure(tmp_path, cfg_defs, monkeypatch):
    config_path = tmp_path / "conf.yml"
    init_config = {vs.config_configfile.config_id: str(config_path)}
    store = vs.ValueStoreFile(cfg_defs, init_config)

    def fail_open(*a, **kw): raise IOError("fail")
    monkeypatch.setattr("builtins.open", fail_open)

    assert store.save_value("item1", "val") is False


# -------------------- ValueStoreEnv --------------------

def test_env_store_retrieve(monkeypatch, cfg_defs):
    store = vs.ValueStoreEnv(cfg_defs)
    monkeypatch.setenv("ENV_VAR1", "ENVVAL")
    val, src = store.retrieve_value("item1")
    assert val == "ENVVAL"
    assert src == vs.ConfigValueSource.ENV_VAR


def test_env_store_retrieve_missing(monkeypatch, cfg_defs):
    store = vs.ValueStoreEnv(cfg_defs)
    monkeypatch.delenv("ENV_VAR1", raising=False)
    val, src = store.retrieve_value("item1")
    assert val is None
    assert src == vs.ConfigValueSource.ENV_VAR


def test_env_store_save_raises(cfg_defs):
    store = vs.ValueStoreEnv(cfg_defs)
    with pytest.raises(NotImplementedError):
        store.save_value("item1", "val")


# -------------------- ValueStoreDefault --------------------

def test_default_store_retrieve(cfg_defs):
    store = vs.ValueStoreDefault(cfg_defs)
    val, src = store.retrieve_value("item1")
    assert val == "default1"
    assert src == vs.ConfigValueSource.DEFAULT

def test_default_store_missing(cfg_defs):
    store = vs.ValueStoreDefault(cfg_defs)
    val, src = store.retrieve_value("item2")
    assert val is None
    assert src == vs.ConfigValueSource.DEFAULT

def test_default_store_save_raises(cfg_defs):
    store = vs.ValueStoreDefault(cfg_defs)
    with pytest.raises(NotImplementedError):
        store.save_value("item1", "val")


# -------------------- ValueStoreSecure --------------------

@pytest.fixture
def mock_securestore(monkeypatch):
    mock_cls = MagicMock()
    mock_instance = MagicMock()
    mock_cls.return_value = mock_instance
    monkeypatch.setattr(vs, "SecureStore", mock_cls)
    return mock_instance

# -------------------- ValueStores factory --------------------

def test_value_stores_get_and_reuse(cfg_defs, tmp_path):
    init_config = {vs.config_configfile.config_id: str(tmp_path / "c.yml")}
    store1 = vs.ValueStores._get(vs.ValueStoreFile, cfg_defs, init_config)
    store2 = vs.ValueStores._get(vs.ValueStoreFile)  # cached
    assert store1 is store2

def test_value_stores_invalid_class():
    with pytest.raises(ValueError):
        vs.ValueStores._get(str)  # not a subclass

def test_value_stores_retrieve_and_save(cfg_defs, tmp_path):
    config_path = tmp_path / "c.yml"
    init_config = {vs.config_configfile.config_id: str(config_path)}
    val, src = vs.ValueStores.retrieve_val(vs.ValueStoreFile, "item1", cfg_defs, init_config)
    assert src == vs.ConfigValueSource.CFGFILE

    result = vs.ValueStores.save_val(vs.ValueStoreFile, "item1", "abc")
    assert result is True
