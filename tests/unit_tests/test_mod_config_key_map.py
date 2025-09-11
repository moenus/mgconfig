# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytest
from mgconfig.config_key_map import ConfigKeyMap, APP, SEC

@pytest.fixture(autouse=True)
def setup_teardown():
    """Clear registry before and after each test."""
    ConfigKeyMap.clear_registry()
    yield
    ConfigKeyMap.clear_registry()

def test_singleton_pattern():
    """Test that ConfigKeyMap maintains singleton behavior per key."""
    key1 = ConfigKeyMap(APP, "test1")
    key2 = ConfigKeyMap(APP, "test1")
    key3 = ConfigKeyMap(APP, "test2")
    
    assert key1 is key2  # Same keys return same instance
    assert key1 is not key3  # Different keys get different instances
    assert key1._registry_key == f"{APP}_test1"
    assert key3._registry_key == f"{APP}_test2"

def test_registry_keys():
    """Test registry key management."""
    key1 = ConfigKeyMap(APP, "test1")
    key2 = ConfigKeyMap(SEC, "test2")
    
    registry_keys = ConfigKeyMap.list_registry_keys()
    assert len(registry_keys) == 2
    assert f"{APP}_test1" in registry_keys
    assert f"{SEC}_test2" in registry_keys

def test_remapping():
    """Test that remapping changes id but not registry key."""
    key = ConfigKeyMap(APP, "test")
    original_id = key.id
    original_registry_key = key._registry_key
    
    # Change mapping
    key.section_prefix = SEC
    key.config_name = "new_test"
    
    assert key.id == f"{SEC}_new_test"  # ID reflects new mapping
    assert key._registry_key == original_registry_key  # Registry key unchanged
    assert str(key) == original_registry_key  # str() shows original key

def test_clear_registry():
    """Test registry clearing functionality."""
    ConfigKeyMap(APP, "test1")
    ConfigKeyMap(SEC, "test2")
    assert len(ConfigKeyMap.list_registry_keys()) == 2
    
    ConfigKeyMap.clear_registry()
    assert len(ConfigKeyMap.list_registry_keys()) == 0

def test_repr_format():
    """Test string representation format."""
    key = ConfigKeyMap(APP, "test")
    key.section_prefix = SEC  # Remap to create difference
    
    expected = f"{APP}_test --> {SEC}_test"
    assert repr(key) == expected

def test_initialization_once():
    """Test that initialization happens only once per unique key."""
    key1 = ConfigKeyMap(APP, "test")
    original_prefix = key1.section_prefix
    
    # Create "new" instance with different prefix
    key2 = ConfigKeyMap(APP, "test")
    key2.section_prefix = "different"
    
    # Both references point to same object
    assert key1.section_prefix == "different"
    assert key1 is key2

@pytest.mark.parametrize("section,name,expected", [
    (APP, "test", f"{APP}_test"),
    (SEC, "key", f"{SEC}_key"),
    ("custom", "item", "custom_item"),
])
def test_id_generation(section, name, expected):
    """Test ID generation with various inputs."""
    key = ConfigKeyMap(section, name)
    assert key.id == expected

def test_mutability():
    """Test that section_prefix and config_name are mutable."""
    key = ConfigKeyMap(APP, "test")
    
    # Can change section_prefix
    key.section_prefix = "new_section"
    assert key.id == "new_section_test"
    
    # Can change config_name
    key.config_name = "new_name"
    assert key.id == "new_section_new_name"
    
    # Original registry key remains unchanged
    assert key._registry_key == f"{APP}_test"