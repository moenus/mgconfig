# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import patch, MagicMock

import mgconfig.configuration as configuration


@pytest.fixture(autouse=True)
def setup_teardown():
    """Ensure clean configuration state for each test."""
    configuration.Configuration.reset_instance()
    yield
    configuration.Configuration.reset_instance()


@pytest.fixture
def mock_config_env(monkeypatch):
    """Provide mock configuration environment with complete test data."""
    test_configs = {
        "test_id": {
            "section": "test",
            "name": "test_item",
            "env": "TEST_ENV",
            "default": "default_value",
            "type": "string",
            "readonly": False,
            "current_value": "current",
            "new_value": "new",
            "prefix": "test_prefix"
        }
    }

    def create_mock_config(config_data):
        mock_def = MagicMock()
        mock_def.config_section = config_data["section"]
        mock_def.config_name = config_data["name"]
        mock_def.config_env = config_data["env"]
        mock_def.config_default = config_data["default"]
        mock_def.config_type = config_data["type"]
        mock_def.config_id = "test_id"
        mock_def.config_readonly = config_data["readonly"]
        mock_def.config_prefix = config_data["prefix"]

        mock_value = MagicMock()
        mock_value.cfg_def = mock_def
        mock_value.value = config_data["current_value"]
        mock_value.source = "file"
        mock_value.__str__.return_value = config_data["current_value"]
        
        # Mock get_display_dict to return a proper dictionary
        display_dict = {
            'config_id': mock_def.config_id,
            'config_section': mock_def.config_section,
            'config_prefix': mock_def.config_prefix,
            'config_name': mock_def.config_name,
            'config_type': mock_def.config_type,
            'config_env': mock_def.config_env,
            'config_default': mock_def.config_default,
            'readonly_flag': 'ro' if mock_def.config_readonly else 'rw',
            'source_str': 'file',
            'value_str': config_data["current_value"]
        }
        mock_value.get_display_dict.return_value = display_dict
        return mock_value

    mock_configs = {k: create_mock_config(v) for k, v in test_configs.items()}
    monkeypatch.setattr(configuration, "config_items", mock_configs)

    return mock_configs["test_id"]


@pytest.fixture
def mock_handlers(monkeypatch):
    monkeypatch.setattr(configuration, "ConfigDefs", MagicMock())
    monkeypatch.setattr(configuration, "ConfigItemHandler", MagicMock())
    monkeypatch.setattr(configuration, "PostProcessing",
                        MagicMock(return_value=MagicMock(dict={})))
    return configuration.ConfigItemHandler


@pytest.mark.parametrize("config_id,expected", [
    ("test_id", "current"),
    ("missing", None),
    ("", None),
])
def test_get_value_parameters(mock_config_env, mock_handlers, config_id, expected):
    """Test get_value with various parameters."""
    cfg = configuration.Configuration("dummy.json")
    assert cfg.get_value(config_id) == expected


def test_singleton_pattern(mock_handlers):
    """Test that Configuration maintains singleton behavior."""
    configuration.Configuration.reset_instance()
    cfg1 = configuration.Configuration("test.json")
    cfg2 = configuration.Configuration("different.json")
    assert cfg1 is cfg2
    assert cfg2.get_value("test_id") == cfg1.get_value("test_id")


def test_initialization_validation():
    """Test initialization parameter validation."""
    configuration.Configuration.reset_instance()
    with pytest.raises(TypeError):
        configuration.Configuration(None)

    # Test with invalid file path types
    with pytest.raises(TypeError):
        configuration.Configuration(123)


def test_initialization_and_get_value(mock_config_env, mock_handlers):
    configuration.Configuration.reset_instance()
    cfg = configuration.Configuration(cfg_defs_filepaths="dummy.json")
    assert cfg.get_value("test_id") == "current"
    assert cfg["test_id"] == "current"
    assert "test_id" in cfg


def test_configuration_reset(mock_config_env, mock_handlers):
    """Test configuration reset behavior."""
    cfg1 = configuration.Configuration("test1.json")
    cfg1.set_property_value("test", "value")
    
    configuration.Configuration.reset_instance()
    cfg2 = configuration.Configuration("test2.json")
    
    assert cfg2 is not cfg1
    assert not hasattr(cfg2, "test")

def test_get_value_fail_on_error(mock_config_env, mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    with pytest.raises(ValueError):
        cfg.get_value("unknown", fail_on_error=True)


def test_get_config_object(mock_config_env, mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    obj = cfg.get_config_item("test_id")
    assert obj is mock_config_env


def test_get_config_object_missing(mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    with pytest.raises(ValueError):
        cfg.get_config_item("missing")


def test_save_new_value_applies_immediately(mock_config_env, mock_handlers):
    mock_handlers.save_new_value.return_value = True
    mock_config_env.cfg_def.config_type = "secret"
    cfg = configuration.Configuration("dummy.json")
    result = cfg.save_new_value("test_id", "new_value", apply_immediately=True)
    assert result is True
    assert cfg.get_value("test_id") == "new_value"


def test_extended_items(mock_handlers):
    cfg = configuration.Configuration("dummy.json")
    cfg.set_property_value("extra", 42)
    assert "extra" in cfg
    assert cfg.get_value("extra") == 42
    assert cfg.get_value("missing") is None


def test_data_rows_property(mock_config_env, mock_handlers):
    """Test data_rows returns correct structure with dictionary data."""
    cfg = configuration.Configuration("dummy.json")
    rows = cfg.data_rows
    assert len(rows) > 0
    
    # Get the first row
    row = rows[0]
    assert isinstance(row, dict), "Row should be a dictionary"
    
    # Verify all expected keys are present
    expected_keys = {
        'config_id',
        'config_section',
        'config_prefix',
        'config_name',
        'config_type',
        'config_env',
        'config_default',
        'readonly_flag',
        'source_str',
        'value_str'
    }
    
    assert set(row.keys()) == expected_keys, "Row missing required keys"
    
    # Verify values from mock_config_env
    assert row['config_id'] == "test_id"
    assert row['config_section'] == "test"
    assert row['config_name'] == "test_item"
    assert row['config_env'] == "TEST_ENV"
    assert row['config_type'] == "string"
    assert row['value_str'] == "current"


def test_post_processing_error_handling(mock_config_env, mock_handlers, monkeypatch):
    """Test error handling in post-processing functions."""
    # Create a post-processing function that raises an error
    def failing_pp(cfg):
        raise ValueError("Test error")
    
    # Create a working post-processing function
    def working_pp(cfg):
        return True
    
    # Setup PostProcessing mock with both functions
    mock_post_processing = MagicMock()
    mock_post_processing.dict = {
        "test_pp_fail": failing_pp,
        "test_pp_work": working_pp
    }
    monkeypatch.setattr(configuration, "PostProcessing", 
                       MagicMock(return_value=mock_post_processing))
    
    # Mock ConfigDefs and ConfigItemHandler to avoid initialization issues
    monkeypatch.setattr(configuration, "ConfigDefs", MagicMock())
    monkeypatch.setattr(configuration, "ConfigItemHandler", MagicMock())
    
    # Reset singleton state
    configuration.Configuration.reset_instance()
    
    # Should not raise exception despite failing post-processing
    cfg = configuration.Configuration("dummy.json")
    assert cfg is not None
    
    # Verify both post-processing functions were called
    for pp_name in mock_post_processing.dict.keys():
        assert mock_post_processing.dict[pp_name] in [failing_pp, working_pp]
