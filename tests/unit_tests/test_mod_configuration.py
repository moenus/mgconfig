import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import mgconfig.configuration as configuration


@pytest.fixture
def mock_config_env(monkeypatch):
    # Mock config_values
    mock_def = MagicMock()
    mock_def.config_section = "section"
    mock_def.config_name = "name"
    mock_def.config_env = "ENV_VAR"
    mock_def.config_default = "default"
    mock_def.config_type = "string"
    mock_def.config_id = "test_id"
    mock_def.config_readonly = False

    mock_value = MagicMock()
    mock_value.cfg_def = mock_def
    mock_value.value = "current"
    mock_value.source = "file"
    mock_value.__str__.return_value = "current"

    monkeypatch.setattr(configuration, "config_values", {"test_id": mock_value})
    monkeypatch.setattr(configuration, "config_values_new", {"test_id": MagicMock(__str__=lambda self: "new")})

    return mock_value


@pytest.fixture
def mock_handlers(monkeypatch):
    monkeypatch.setattr(configuration, "ConfigDefs", MagicMock())
    monkeypatch.setattr(configuration, "ConfigValueHandler", MagicMock())
    monkeypatch.setattr(configuration, "PostProcessing", MagicMock(return_value=MagicMock(dict={})))
    return configuration.ConfigValueHandler


def test_initialization_and_get_value(mock_config_env, mock_handlers):
    configuration.Configuration.reset_instance()
    cfg = configuration.Configuration(cfg_defs_filepaths="dummy.json")
    assert cfg.get_value("test_id") == "current"
    assert cfg["test_id"] == "current"
    assert "test_id" in cfg


def test_get_value_fail_on_error(mock_config_env, mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    with pytest.raises(ValueError):
        cfg.get_value("unknown", fail_on_error=True)


def test_get_config_object(mock_config_env, mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    obj = cfg.get_config_object("test_id")
    assert obj is mock_config_env


def test_get_config_object_missing(mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    with pytest.raises(ValueError):
        cfg.get_config_object("missing")


def test_data_rows_contains_current_and_new(mock_config_env, mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    rows = cfg.data_rows
    assert any("current" in row for row in rows)
    assert any("new" in row for row in rows)


def test_save_new_value_applies_immediately(mock_config_env, mock_handlers):
    mock_handlers.save_new_value.return_value = True
    mock_config_env.cfg_def.config_type = "secret"
    cfg = configuration.Configuration("dummy.json")
    result = cfg.save_new_value("test_id", "new_value", apply_immediately=True)
    assert result is True
    assert cfg.get_value("test_id") == "new_value"


def test_extended_items(mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    cfg.set_extended_item("extra", 42)
    assert cfg.extended_item_exists("extra")
    assert cfg.get_extended_item("extra") == 42
    assert cfg.get_extended_item("missing") is None
