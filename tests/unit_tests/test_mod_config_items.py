from unittest.mock import MagicMock
import pytest
from dataclasses import dataclass
from mgconfig.config_items import ConfigItem, ConfigItems, config_items, config_items_new

# -----------------------------
# Fixtures
# -----------------------------
@dataclass
class MockConfigDef:
    """Mock ConfigDef for testing."""
    config_id: str = "test_id"
    config_section: str = "test_section"
    config_prefix: str = "test_prefix"
    config_name: str = "test_name"
    config_type: str = "str"
    config_env: str = "TEST_ENV"
    config_default: str = "default"
    config_readonly: bool = False

@pytest.fixture
def config_def():
    """Provide mock config definition."""
    return MockConfigDef()

@pytest.fixture
def config_item(config_def):
    """Provide test config item."""
    return ConfigItem(config_def, "test_value", "test_source")

@pytest.fixture
def items_collection():
    """Provide test items collection."""
    items = ConfigItems()
    return items

# -----------------------------
# ConfigItem Tests
# -----------------------------
def test_config_item_initialization(config_def):
    """Test ConfigItem initialization."""
    item = ConfigItem(config_def, "test_value", "test_source", True)
    
    assert item.value == "test_value"
    assert item.source == "test_source"
    assert item.new is True
    assert item.config_id == config_def.config_id
    assert item.config_section == config_def.config_section

def test_config_item_str_representation(config_item):
    """Test string representation of ConfigItem."""
    assert str(config_item) == "test_value"
    assert config_item.value_str == "test_value"

def test_config_item_source_str(config_def):
    """Test source string representation."""
    item1 = ConfigItem(config_def, source="env")
    assert item1.source_str == "env"
    
    item2 = ConfigItem(config_def, new=True)
    assert item2.source_str == "new"

def test_config_item_readonly_flag(config_def):
    """Test readonly flag."""
    config_def.config_readonly = True
    ro_item = ConfigItem(config_def)
    assert ro_item.readonly_flag == "ro"
    
    config_def.config_readonly = False
    rw_item = ConfigItem(config_def)
    assert rw_item.readonly_flag == "rw"

def test_config_item_display_dict(config_item):
    """Test display dictionary generation."""
    display_dict = config_item.get_display_dict()
    
    assert isinstance(display_dict, dict)
    assert display_dict["config_id"] == "test_id"
    assert display_dict["value_str"] == "test_value"
    assert display_dict["source_str"] == "test_source"
    assert display_dict["readonly_flag"] == "rw"

# -----------------------------
# ConfigItems Tests
# -----------------------------
def test_config_items_set_valid(items_collection, config_item):
    """Test setting valid config item."""
    items_collection.set("test_key", config_item)
    assert "test_key" in items_collection
    assert items_collection["test_key"] is config_item

def test_config_items_set_invalid(items_collection):
    """Test setting invalid item raises TypeError."""
    with pytest.raises(TypeError, match="Item for configuration key .* invalid"):
        items_collection.set("test_key", "not_a_config_item")

def test_config_items_get_existing(items_collection, config_item):
    """Test getting existing item."""
    items_collection["test_key"] = config_item
    assert items_collection.get("test_key") is config_item

def test_config_items_get_nonexistent(items_collection):
    """Test getting non-existent item."""
    assert items_collection.get("missing_key") is None
    
    with pytest.raises(KeyError, match="Item for configuration key .* not found"):
        items_collection.get("missing_key", fail_on_error=True)

def test_config_items_get_value(items_collection, config_item):
    """Test getting item value."""
    items_collection["test_key"] = config_item
    
    assert items_collection.get_value("test_key") == "test_value"
    assert items_collection.get_value("missing_key") is None
    assert items_collection.get_value("missing_key", default="default") == "default"
    
    with pytest.raises(KeyError):
        items_collection.get_value("missing_key", fail_on_error=True)

def test_config_items_to_dict(items_collection, config_item):
    """Test converting to plain dictionary."""
    items_collection["test_key"] = config_item
    items_collection["another_key"] = ConfigItem(
        MockConfigDef(), "another_value", "another_source"
    )
    
    result = items_collection.to_dict()
    assert isinstance(result, dict)
    assert result == {
        "test_key": "test_value",
        "another_key": "another_value"
    }

# -----------------------------
# Global Instances Tests
# -----------------------------
def test_global_config_items_instances():
    """Test global ConfigItems instances."""
    assert isinstance(config_items, ConfigItems)
    assert isinstance(config_items_new, ConfigItems)
    assert config_items != config_items_new  # Different instances