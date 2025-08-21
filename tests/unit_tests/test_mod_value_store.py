import os
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import mgconfig.value_stores as vs


@pytest.fixture
def mock_cfg_def():
    """Fixture returning a fake ConfigDef object with get_property()."""
    class DummyCfgDef:
        config_id = "test_id"
        config_type = "str"
        config_default = "default_val"
        config_readonly = False

        def get_property(self, property_name: str):
            if not hasattr(self, property_name):
                raise KeyError(f"{property_name} invalid.")
            return getattr(self, property_name)

    return DummyCfgDef()


@pytest.fixture
def mock_cfg_defs(mock_cfg_def):
    """Fixture returning a fake ConfigDefs mapping {id: ConfigDef}."""
    return {mock_cfg_def.config_id: mock_cfg_def}


@pytest.fixture
def cfg_defs():
    class DummyCfgDef:
        def __init__(self, cid, ctype, default="defaultval", env="envvar", readonly=False, section="section1", name="name1"):
            self.config_id = cid
            self.config_type = ctype
            self.config_default = default
            self.config_readonly = readonly
            self.config_section = section
            self.config_name = name
            self.config_env = env

        def get_property(self, name):
            if name not in self.__dict__:
                raise KeyError(f"{name} invalid")
            return getattr(self, name)

    return {
        "item1": DummyCfgDef("key1", "str", env="ENV_VAR1", default="default1", section = "section1", name= "name1"),
        "item2": DummyCfgDef("key2", "secret", default = None, section = "section1", name= "name2"),
    }


# -------------------- ValueStoreFile --------------------

def test_file_store_read_and_write(tmp_path, cfg_defs):
    config_path = tmp_path / "config.yml"
    init_config = {vs.config_configfile.config_id: str(config_path)}

    store = vs.ValueStoreFile(cfg_defs, init_config)

    # Initially empty
    assert store.retrieve_value("item1") == (
        None, vs.ConfigValueSource.CFGFILE)

    # Save and check file contents
    assert store.save_value("item1", "myvalue") is True
    with open(config_path) as f:
        data = yaml.safe_load(f)
    assert data["section1"]["name1"] == "myvalue"

    # Retrieval works
    val, src = store.retrieve_value("item1")
    assert val == "myvalue"
    assert src == vs.ConfigValueSource.CFGFILE


def test_file_store_missing_file(tmp_path, cfg_defs):
    init_config = {vs.config_configfile.config_id: str(
        tmp_path / "doesnotexist.yml")}
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
    val, src = store.retrieve_value("name1")
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
    val, src = vs.ValueStores.retrieve_val(
        vs.ValueStoreFile, "item1", cfg_defs, init_config)
    assert src == vs.ConfigValueSource.CFGFILE

    result = vs.ValueStores.save_val(vs.ValueStoreFile, "item1", "abc")
    assert result is True
