# test_config_defs.py
# Unit tests for config_defs.py

import pytest
import keyword
import tempfile
import yaml
from pathlib import Path
from mgconfig.config_defs import CDF, ConfigDef, DefDict, ConfigDefs
from mgconfig.config_defs import DefaultFunctions, DefaultValues, ConfigTypes


# ----------------------------
# Fixtures and helpers
# ----------------------------

@pytest.fixture
def valid_config_def_data():
    return [
        {
            "section": "general",
            "prefix": "app",
            "configs": [
                {
                    "name": "port",
                    "type": "int",
                    "default": 8080,
                    "description": "Application port",
                    "readonly": False
                }
            ]
        }
    ]


@pytest.fixture
def temp_yaml_file(valid_config_def_data, tmp_path):
    """Create a temporary YAML file with valid config data."""
    path = tmp_path / "config.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(valid_config_def_data, f)
    return path


# ----------------------------
# Tests for CDF
# ----------------------------

def test_cdf_str_and_src_name():
    assert str(CDF.NAME) == "config_name"
    assert CDF.NAME.src_name == "name"


def test_cdf_enum_members_exist():
    assert "section" in [c.value for c in CDF]
    assert "default_function" in [c.value for c in CDF]


# ----------------------------
# Tests for ConfigDef
# ----------------------------

def test_configdef_valid():
    cfg = ConfigDef(
        config_id="app_port",
        config_type="int",
        config_readonly=False,
        config_name="port",
        config_prefix="app",
        config_section="general",
        config_default=8080,
    )
    assert cfg.config_id == "app_port"
    assert cfg.get_property("config_name") == "port"


def test_configdef_invalid_identifier():
    with pytest.raises(ValueError):
        ConfigDef(
            config_id="1notvalid",
            config_type="int",
            config_readonly=False,
            config_name="port",
            config_prefix="app",
            config_section="general"
        )


def test_configdef_keyword_identifier():
    kw = keyword.kwlist[0]
    with pytest.raises(ValueError):
        ConfigDef(
            config_id=kw,
            config_type="int",
            config_readonly=False,
            config_name="port",
            config_prefix="app",
            config_section="general"
        )


def test_configdef_invalid_type():
    with pytest.raises(ValueError):
        ConfigDef(
            config_id="app_port",
            config_type="nonexistent",
            config_readonly=False,
            config_name="port",
            config_prefix="app",
            config_section="general"
        )


def test_configdef_default_value_mismatch():
    with pytest.raises(ValueError):
        ConfigDef(
            config_id="app_port",
            config_type="int",
            config_readonly=False,
            config_name="port",
            config_prefix="app",
            config_section="general",
            config_default="not_an_int",
        )


def test_configdef_readonly_must_be_bool():
    with pytest.raises(ValueError):
        ConfigDef(
            config_id="app_port",
            config_type="int",
            config_readonly="yes",
            config_name="port",
            config_prefix="app",
            config_section="general"
        )


def test_configdef_mandatory_string_fields():
    with pytest.raises(ValueError):
        ConfigDef(
            config_id="",
            config_type="int",
            config_readonly=False,
            config_name="port",
            config_prefix="app",
            config_section="general"
        )


def test_configdef_get_property_invalid():
    cfg = ConfigDef(
        config_id="app_port",
        config_type="int",
        config_readonly=False,
        config_name="port",
        config_prefix="app",
        config_section="general",
        config_default=8080,
    )
    with pytest.raises(KeyError):
        cfg.get_property("not_a_field")


# ----------------------------
# Tests for DefDict
# ----------------------------

def test_defdict_set_and_get():
    d = DefDict()
    d.set(CDF.NAME, "port")
    assert d.get(CDF.NAME) == "port"


def test_defdict_get_invalid_key_type():
    d = DefDict()
    with pytest.raises(KeyError):
        d.get("not_a_cdf")


def test_defdict_get_not_found():
    d = DefDict()
    with pytest.raises(KeyError):
        d.get(CDF.NAME)


def test_defdict_set_invalid_key_type():
    d = DefDict()
    with pytest.raises(KeyError):
        d.set("not_a_cdf", "value")


# ----------------------------
# Tests for ConfigDefs
# ----------------------------

def test_configdefs_load_valid(temp_yaml_file):
    cfg_defs = ConfigDefs(temp_yaml_file)
    assert "app_port" in cfg_defs
    assert isinstance(cfg_defs["app_port"], ConfigDef)


def test_configdefs_invalid_yaml_structure(tmp_path):
    path = tmp_path / "invalid.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({"notalist": "value"}, f)
    with pytest.raises(ValueError):
        ConfigDefs(path)


def test_configdefs_invalid_prefix(temp_yaml_file, valid_config_def_data):
    # modify prefix to be invalid
    valid_config_def_data[0]["prefix"] = "_badprefix"
    path = temp_yaml_file
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(valid_config_def_data, f)
    with pytest.raises(ValueError):
        ConfigDefs(path)


def test_configdefs_duplicate_definition(tmp_path, valid_config_def_data):
    # add duplicate config with same id
    valid_config_def_data[0]["configs"].append({
        "name": "port",
        "type": "int"
    })
    path = tmp_path / "dup.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(valid_config_def_data, f)
    with pytest.raises(ValueError):
        ConfigDefs(path)


def test_configdefs_default_function(monkeypatch, tmp_path, valid_config_def_data):
    def fake_function():
        return 9999

    monkeypatch.setattr(DefaultFunctions, "contains", lambda self, name: True)
    monkeypatch.setattr(DefaultFunctions, "get", lambda self, name: fake_function)

    valid_config_def_data[0]["configs"][0]["default_function"] = "fake"
    path = tmp_path / "func.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(valid_config_def_data, f)

    cfg_defs = ConfigDefs(path)
    assert cfg_defs["app_port"].config_default == 9999


def test_configdefs_default_function_not_callable(monkeypatch, tmp_path, valid_config_def_data):
    monkeypatch.setattr(DefaultFunctions, "contains", lambda self, name: True)
    monkeypatch.setattr(DefaultFunctions, "get", lambda self, name: 123)

    valid_config_def_data[0]["configs"][0]["default_function"] = "fake"
    path = tmp_path / "func.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(valid_config_def_data, f)

    with pytest.raises(ValueError):
        ConfigDefs(path)


def test_configdefs_default_from_defaultvalues(monkeypatch, tmp_path, valid_config_def_data):
    monkeypatch.setattr(DefaultFunctions, "contains", lambda self, name: False)
    monkeypatch.setattr(DefaultValues, "dict", {"app_port": 123})
    monkeypatch.setattr(DefaultValues, "get", lambda self, key: 123)

    del valid_config_def_data[0]["configs"][0]["default"]
    path = tmp_path / "val.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(valid_config_def_data, f)

    cfg_defs = ConfigDefs(path)
    assert cfg_defs["app_port"].config_default == 123


def test_configdefs_mapping_methods(temp_yaml_file):
    cfg_defs = ConfigDefs(temp_yaml_file)

    assert "app_port" in cfg_defs
    assert list(cfg_defs.keys()) == ["app_port"]
    assert isinstance(list(cfg_defs.values())[0], ConfigDef)
    assert list(cfg_defs.items())[0][0] == "app_port"
    assert len(cfg_defs) == 1

    cfg = cfg_defs.get("app_port")
    assert isinstance(cfg, ConfigDef)

    cfg2 = ConfigDef(
        config_id="app_debug",
        config_type="bool",
        config_readonly=False,
        config_name="debug",
        config_prefix="app",
        config_section="general",
        config_default=True
    )
    cfg_defs["app_debug"] = cfg2
    assert "app_debug" in cfg_defs
    del cfg_defs["app_debug"]
    assert "app_debug" not in cfg_defs
