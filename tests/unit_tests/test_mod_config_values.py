# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

# import pytest
# from mgconfig.config_values import config_values

# class DummyConfigValue:
#     def __init__(self, value):
#         self.value = value
#         self.cleaned_up = False
        
#     def cleanup(self):
#         self.cleaned_up = True

# @pytest.fixture(autouse=True)
# def setup():
#     """Clear ConfigValues before and after each test"""
#     config_values.clear()
#     yield
#     config_values.clear()

# def test_add_and_get():
#     """Test adding and retrieving values"""
#     value = DummyConfigValue("test")
#     config_values.set("test_key", value)
#     assert config_values.get("test_key") == value


# def test_contains():
#     """Test key existence check"""
#     config_values.set("test_key", DummyConfigValue("test"))
#     assert ConfigValues.contains("test_key")
#     assert not ConfigValues.contains("missing_key")

# def test_keys_values_items():
#     """Test dictionary methods"""
#     value1 = DummyConfigValue("test1")
#     value2 = DummyConfigValue("test2")
#     config_values.set("key1", value1)
#     config_values.set("key2", value2)
    
#     assert set(ConfigValues.keys()) == {"key1", "key2"}
#     assert list(config_values.values()) == [value1, value2]
#     assert set(config_values.items()) == {("key1", value1), ("key2", value2)}

# def test_iteration():
#     """Test iteration over ConfigValues"""
#     items = {"key1": DummyConfigValue("test1"), 
#              "key2": DummyConfigValue("test2")}
#     for k, v in items.items():
#         config_values.set(k, v)
    
#     assert set(ConfigValues) == set(items.keys())

# def test_len():
#     """Test length calculation"""
#     config_values.set("key1", DummyConfigValue("test1"))
#     config_values.set("key2", DummyConfigValue("test2"))
#     assert len(ConfigValues) == 2

# def test_get_with_default():
#     """Test get with default value"""
#     default = DummyConfigValue("default")
#     assert config_values.get("missing", default) == default

# def test_get_with_fail_on_error():
#     """Test get with fail_on_error"""
#     with pytest.raises(KeyError):
#         config_values.get("missing", fail_on_error=True)

# def test_delete_item():
#     """Test item deletion"""
#     config_values.set("test_key", DummyConfigValue("test"))
#     del ConfigValues["test_key"]
#     assert not ConfigValues.contains("test_key")

# def test_clear():
#     """Test clearing all values"""
#     value1 = DummyConfigValue("test1")
#     value2 = DummyConfigValue("test2")
#     config_values.set("key1", value1)
#     config_values.set("key2", value2)
    
#     config_values.clear()
#     assert len(ConfigValues) == 0
#     assert value1.cleaned_up
#     assert value2.cleaned_up

# def test_dict_property():
#     """Test dict property access"""
#     value = DummyConfigValue("test")
#     config_values.set("test_key", value)
#     assert ConfigValues.dict["test_key"] == value