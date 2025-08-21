# test_configuration.py
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mgconfig.configuration


@pytest.fixture(autouse=True)
def reset_configuration():
    """Ensure singleton is reset before/after each test."""
    mgconfig.configuration.Configuration.reset()
    yield
    mgconfig.configuration.Configuration.reset()


@pytest.fixture
def mock_cfg_defs_and_values():
    # Mock ConfigDef
    mock_cfg_def = MagicMock()
    mock_cfg_def.config_section = "section"
    mock_cfg_def.config_name = "name"
    mock_cfg_def.config_env = "ENV_VAR"
    mock_cfg_def.config_default = "default"
    mock_cfg_def.config_type = "str"
    mock_cfg_def.config_id = "test_id"
    mock_cfg_def.config_readonly = False

    # Mock ConfigValue
    mock_cfg_value = MagicMock()
    mock_cfg_value.value = "value"
    mock_cfg_value.value_new = None
    mock_cfg_value.source = "default"
    mock_cfg_value.display_current.return_value = "value"
    mock_cfg_value.display_new.return_value = "new_value"

    # Mock ConfigValues
    mock_cfg_values = MagicMock()
    mock_cfg_values.__getitem__.return_value = mock_cfg_value
    mock_cfg_values.__contains__.side_effect = lambda key: key == "test_id"
    mock_cfg_values.__iter__.return_value = iter(["test_id"])
    mock_cfg_values.save_new_value = MagicMock()

    # Patch imports inside configuration
    with patch("mgconfig.configuration.ConfigDefs", return_value={"test_id": mock_cfg_def}), \
         patch("mgconfig.configuration.ConfigValues", return_value=mock_cfg_values), \
         patch("mgconfig.configuration.PostProcessing", return_value=MagicMock(dict={})):
        yield mock_cfg_def, mock_cfg_value, mock_cfg_values


def test_singleton_behavior(mock_cfg_defs_and_values):
    cfg1 = mgconfig.configuration.Configuration("file")
    cfg2 = mgconfig.configuration.Configuration("file")
    assert cfg1 is cfg2  # singleton must return same instance


def test_init_sets_attributes(mock_cfg_defs_and_values):
    _, mock_cfg_value, _ = mock_cfg_defs_and_values
    cfg = mgconfig.configuration.Configuration("file")
    # attribute from config values is set on instance
    assert cfg.test_id == mock_cfg_value.value
    # extended namespace created
    assert isinstance(cfg.extended, SimpleNamespace)


def test_get_existing_and_missing(mock_cfg_defs_and_values):
    cfg = mgconfig.configuration.Configuration("file")
    assert cfg.get("test_id") == "value"
    assert cfg.get("missing") is None
    with pytest.raises(ValueError):
        cfg.get("missing", fail_on_error=True)


def test_get_config_value(mock_cfg_defs_and_values):
    _, mock_cfg_value, _ = mock_cfg_defs_and_values
    cfg = mgconfig.configuration.Configuration("file")
    assert cfg.get_config_value("test_id") is mock_cfg_value
    with pytest.raises(ValueError):
        cfg.get_config_value("missing")


def test_get_cfg_def(mock_cfg_defs_and_values):
    mock_cfg_def, _, _ = mock_cfg_defs_and_values
    cfg = mgconfig.configuration.Configuration("file")
    assert cfg.get_cfg_def("test_id") is mock_cfg_def
    with pytest.raises(ValueError):
        cfg.get_cfg_def("missing")


def test_data_rows_without_new_value(mock_cfg_defs_and_values):
    cfg = mgconfig.configuration.Configuration("file")
    rows = cfg.data_rows
    assert len(rows) == 1
    assert rows[0][1] == "name"  # config_name


def test_data_rows_with_new_value(mock_cfg_defs_and_values):
    _, mock_cfg_value, _ = mock_cfg_defs_and_values
    mock_cfg_value.value_new = "something"
    cfg = mgconfig.configuration.Configuration("file")
    rows = cfg.data_rows
    assert len(rows) == 2
    # second row should use display_new
    assert rows[1][5] == "new_value"


def test_save_new_value_apply_immediately(mock_cfg_defs_and_values):
    _, mock_cfg_value, mock_cfg_values = mock_cfg_defs_and_values
    cfg = mgconfig.configuration.Configuration("file")
    cfg.save_new_value("test_id", "new_val", apply_immediately=True)

    mock_cfg_values.save_new_value.assert_called_once_with("test_id", "new_val", True)
    # attribute was updated from ConfigValue.value
    assert cfg.test_id == mock_cfg_value.value


def test_save_new_value_no_apply(mock_cfg_defs_and_values):
    _, mock_cfg_value, mock_cfg_values = mock_cfg_defs_and_values
    cfg = mgconfig.configuration.Configuration("file")
    cfg.save_new_value("test_id", "new_val", apply_immediately=False)

    mock_cfg_values.save_new_value.assert_called_once_with("test_id", "new_val", False)
    # instance attribute stays the same
    assert cfg.test_id == mock_cfg_value.value


def test_extended_items(mock_cfg_defs_and_values):
    cfg = mgconfig.configuration.Configuration("file")
    assert not cfg.extended_item_exists("foo")
    cfg.set_extended_item("foo", 123)
    assert cfg.extended_item_exists("foo")
    assert cfg.get_extended_item("foo") == 123
    assert cfg.get_extended_item("bar") is None
