# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
import yaml
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, mock_open, MagicMock

import builtins

# --- Imports from your module ---
from mgconfig.config_defs import ConfigDefs, ConfigDef, CONFIG_PREFIX, CDF


@pytest.fixture(autouse=True)
def mock_config_types(monkeypatch):
    ConfigDefs.reset_instance()
    mock_ct = MagicMock()
    mock_ct._config_types = ["string", "int"]
    mock_ct.parse_value.side_effect = lambda value, t: (isinstance(
        value, str) if t == "string" else isinstance(value, int), None)
    monkeypatch.setattr("mgconfig.config_defs.ConfigTypes", mock_ct)
    return mock_ct


@pytest.fixture
def mock_defaults(monkeypatch):
    mock_funcs = MagicMock()
    mock_funcs.get.side_effect = lambda name: (
        lambda: "func_default") if name == "use_func" else None
    monkeypatch.setattr(
        "mgconfig.config_defs.DefaultFunctions", lambda: mock_funcs)

    mock_vals = MagicMock()
    mock_vals.dict = {"prefix_name": "val_default"}
    mock_vals.get.side_effect = lambda key: mock_vals.dict.get(key)
    monkeypatch.setattr(
        "mgconfig.config_defs.DefaultValues", lambda: mock_vals)

    return mock_funcs, mock_vals


def make_yaml_data(valid=True):
    if valid:
        return [{
            "section": "sec",
            "prefix": "prefix",
            "configs": [{
                "name": "name",
                "type": "string",
                "default": "abc",
                "env": "ENVVAR",
                "description": "desc",
                "readonly": True
            }]
        }]
    else:
        return {"not": "a list"}


def test_parse_config_defs_success(tmp_path, mock_defaults):
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(yaml.safe_dump(make_yaml_data()), encoding="utf-8")

    cfg = ConfigDefs(yaml_path)
    expected_config_id = "prefix_name"  # Matches section_prefix_name pattern
    assert expected_config_id in cfg.cfg_defs
    cfg_def = cfg.cfg_defs[expected_config_id]
    assert isinstance(cfg_def, ConfigDef)
    assert cfg_def.config_default == "val_default"  # comes from mock_vals.dict

def test_parse_with_default_values(tmp_path, mock_defaults):
    data = make_yaml_data()
    # matches prefix_name in mock_vals.dict
    data[0]["configs"][0]["name"] = "name"
    data[0]["configs"][0].pop("default", None)
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    cfg = ConfigDefs(yaml_path)
    assert cfg.cfg_defs["prefix_name"].config_default == "val_default"


def test_invalid_yaml_structure(tmp_path):
    ConfigDefs.reset_instance()
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(yaml.safe_dump(
        make_yaml_data(valid=False)), encoding="utf-8")
    with pytest.raises(ValueError) as e:
        ConfigDefs(yaml_path)
    assert "expected a list" in str(e.value)


def test_invalid_prefix_raises(tmp_path):
    ConfigDefs.reset_instance()
    data = make_yaml_data()
    data[0]["prefix"] = "_bad"
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError) as e:
        ConfigDefs(yaml_path)
    assert "invalid section prefix" in str(e.value)


def test_duplicate_config_id_raises(tmp_path):
    ConfigDefs.reset_instance()
    data = make_yaml_data()
    data.append(make_yaml_data()[0])
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ValueError) as e:
        ConfigDefs(yaml_path)
    assert "Duplicate definition" in str(e.value)


# --- ConfigDef validation tests ---

def test_invalid_identifier(monkeypatch):
    monkeypatch.setattr(
        "mgconfig.config_defs.ConfigTypes._config_types", ["string"])
    with pytest.raises(ValueError) as e:
        ConfigDef(config_id="1bad", config_type="string", config_readonly=True,
                  config_name="name", config_prefix="pre", config_section="sec")
    assert "not a valid Python identifier" in str(e.value)


def test_invalid_type_in_config_def(monkeypatch):
    monkeypatch.setattr(
        "mgconfig.config_defs.ConfigTypes._config_types", ["string"])
    with pytest.raises(ValueError) as e:
        ConfigDef(config_id="valid", config_type="wrong", config_readonly=True,
                  config_name="name", config_prefix="pre", config_section="sec")
    assert "config type 'wrong' is invalid" in str(e.value)


def test_default_value_type_mismatch(monkeypatch):
    monkeypatch.setattr(
        "mgconfig.config_defs.ConfigTypes._config_types", ["int"])
    monkeypatch.setattr(
        "mgconfig.config_defs.ConfigTypes.parse_value", lambda v, t: (False, None))
    with pytest.raises(ValueError) as e:
        ConfigDef(config_id="valid", config_type="int", config_readonly=True,
                  config_name="name", config_prefix="pre", config_section="sec",
                  config_default="abc")
    assert "default value type does not match" in str(e.value)


def test_readonly_not_bool():
    with pytest.raises(ValueError) as e:
        ConfigDef(config_id="valid", config_type="string", config_readonly="yes",
                  config_name="name", config_prefix="pre", config_section="sec")
    assert "must be a boolean" in str(e.value)


def test_mandatory_string_fields_empty():
    with pytest.raises(ValueError) as e:
        ConfigDef(config_id="valid", config_type="string", config_readonly=True,
                  config_name="", config_prefix="pre", config_section="sec")
    assert "must be a non-empty string" in str(e.value)
