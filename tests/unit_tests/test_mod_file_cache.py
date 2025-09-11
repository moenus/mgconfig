# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
from types import MappingProxyType

from mgconfig.file_cache import (
    FileCache, FileFormat, FileMode, get_file_format,
    open_secure_file
)

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "string": "value",
        "number": 42,
        "list": [1, 2, 3],
        "nested": {"key": "value"}
    }

@pytest.fixture
def temp_json_file(tmp_path, sample_data):
    """Create a temporary JSON file with sample data."""
    filepath = tmp_path / "test.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f)
    return filepath

@pytest.fixture
def temp_yaml_file(tmp_path, sample_data):
    """Create a temporary YAML file with sample data."""
    filepath = tmp_path / "test.yaml"
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.safe_dump(sample_data, f)
    return filepath

# -----------------------------
# FileFormat Tests
# -----------------------------
@pytest.mark.parametrize("filename,expected", [
    ("test.json", FileFormat.JSON),
    ("test.yaml", FileFormat.YAML),
    ("test.yml", FileFormat.YAML),
    ("TEST.JSON", FileFormat.JSON),
    ("TEST.YAML", FileFormat.YAML),
])
def test_get_file_format(filename, expected):
    """Test file format detection from various extensions."""
    assert get_file_format(Path(filename)) == expected

def test_get_file_format_invalid():
    """Test invalid file format detection."""
    with pytest.raises(ValueError, match="Unsupported file extension"):
        get_file_format(Path("test.txt"))

# -----------------------------
# Cache Initialization Tests
# -----------------------------
def test_initialization_with_format():
    """Test initialization with explicit format."""
    cache = FileCache(Path("test.dat"), FileFormat.JSON)
    assert cache._file_format == FileFormat.JSON
    assert cache._file_mode == FileMode.STANDARD_WRITE

def test_initialization_invalid_path():
    """Test initialization with invalid path type."""
    with pytest.raises(ValueError, match="not a PATH instance"):
        FileCache("not/a/path")

def test_cache_repr():
    """Test string representation."""
    cache = FileCache(Path("test.json"))
    repr_str = repr(cache)
    assert "test.json" in repr_str
    assert "json" in repr_str
    assert "std" in repr_str

# -----------------------------
# Data Access Tests
# -----------------------------
def test_data_property_readonly(temp_json_file, sample_data):
    """Test data property in readonly mode."""
    cache = FileCache(temp_json_file, FileFormat.JSON, FileMode.READONLY)
    data = cache.data
    assert isinstance(data, MappingProxyType)
    assert dict(data) == sample_data

def test_data_property_standard(temp_json_file, sample_data):
    """Test data property in standard mode."""
    cache = FileCache(temp_json_file)
    assert cache.data == sample_data
    assert not isinstance(cache.data, MappingProxyType)

def test_clear_cache():
    """Test cache clearing."""
    cache = FileCache(Path("test.json"))
    cache._data = {"test": "value"}
    cache._ready = True
    
    cache.clear()
    assert cache._data == {}
    assert not cache._ready

# -----------------------------
# File Operations Tests
# -----------------------------
def test_yaml_write_and_read(tmp_path: Path, sample_data):
    """Test YAML write and read operations."""
    filepath = tmp_path / "test.yaml"
    cache = FileCache(filepath, FileFormat.YAML)
    
    cache._data = sample_data.copy()
    cache._ready = True
    cache.save()
    
    # Verify YAML format
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
        assert ":" in content  # Basic YAML formatting check
    
    # Read back
    new_cache = FileCache(filepath, FileFormat.YAML)
    assert new_cache.data == sample_data

@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_secure_write_windows(tmp_path: Path, sample_data):
    """Test secure write mode on Windows."""
    filepath = tmp_path / "secure.json"
    cache = FileCache(filepath, FileFormat.JSON, FileMode.SECURE_WRITE)
    
    cache._data = sample_data
    cache._ready = True
    cache.save()
    
    assert filepath.exists()
    # Verify content
    with open(filepath, encoding='utf-8') as f:
        assert json.load(f) == sample_data

def test_atomic_write_cleanup(tmp_path: Path, sample_data):
    """Test atomic write cleanup on error."""
    filepath = tmp_path / "atomic.json"
    cache = FileCache(filepath, FileFormat.JSON, FileMode.ATOMIC_WRITE)
    cache._data = sample_data
    cache._ready = True
    
    with patch('tempfile.NamedTemporaryFile', side_effect=Exception("Test error")):
        with pytest.raises(RuntimeError, match="Atomic write failed"):
            cache.save()
    
    # Verify no temporary files left behind
    temp_files = list(tmp_path.glob("tmp*"))
    assert len(temp_files) == 0
    
    # Verify no temporary files left behind
    temp_files = list(tmp_path.glob("tmp*"))
    assert len(temp_files) == 0

# -----------------------------
# Error Handling Tests
# -----------------------------
def test_yaml_parse_error(tmp_path: Path):
    """Test YAML parsing error handling."""
    filepath = tmp_path / "invalid.yaml"
    filepath.write_text("{{invalid: yaml: }")
    
    cache = FileCache(filepath, FileFormat.YAML)
    with pytest.raises(RuntimeError, match="Cannot read values"):
        _ = cache.data

def test_file_permission_error_on_read(tmp_path: Path):
    """Test permission error handling during read."""
    filepath = tmp_path / "noperm.json"
    filepath.touch()
    
    with patch('builtins.open', side_effect=PermissionError):
        cache = FileCache(filepath)
        with pytest.raises(RuntimeError, match="Cannot read values"):
            _ = cache.data

# -----------------------------
# Context Manager Tests
# -----------------------------
def test_context_manager_exception_handling(tmp_path: Path):
    """Test context manager exception handling."""
    filepath = tmp_path / "context.json"
    
    with pytest.raises(ValueError, match="Test error"):
        with FileCache(filepath) as cache:
            cache._data = {"test": "value"}
            cache._ready = True
            raise ValueError("Test error")
    
    # Verify file wasn't created due to error
    assert not filepath.exists()

def test_context_manager_successful_save(tmp_path: Path, sample_data):
    """Test successful context manager operation."""
    filepath = tmp_path / "context.json"
    
    with FileCache(filepath) as cache:
        cache._data = sample_data.copy()
        cache._ready = True
    
    # Verify file was saved correctly
    assert filepath.exists()
    with open(filepath, encoding='utf-8') as f:
        assert json.load(f) == sample_data