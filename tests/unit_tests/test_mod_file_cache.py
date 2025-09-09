import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import os
from mgconfig.file_cache import FileCache, FileFormat, FileMode, get_file_format

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

# -----------------------------
# FileFormat Tests
# -----------------------------
def test_file_format_values():
    """Test FileFormat enum values."""
    assert FileFormat.JSON.value == 'json'
    assert FileFormat.YAML.value == 'yaml'

def test_get_file_format():
    """Test file format detection from extensions."""
    assert get_file_format(Path("test.json")) == FileFormat.JSON
    assert get_file_format(Path("test.yaml")) == FileFormat.YAML
    assert get_file_format(Path("test.yml")) == FileFormat.YAML
    
    with pytest.raises(ValueError, match="Unsupported file extension"):
        get_file_format(Path("test.txt"))

# -----------------------------
# Basic Cache Operations
# -----------------------------
def test_initialization():
    """Test basic cache initialization."""
    cache = FileCache(Path("test.json"))
    assert cache._ready is False
    assert cache._data == {}
    assert cache._file_format == FileFormat.JSON
    assert cache._file_mode == FileMode.STANDARD_WRITE

def test_invalid_filepath_type():
    """Test initialization with invalid filepath type."""
    with pytest.raises(ValueError, match="not a PATH instance"):
        FileCache("not/a/path")

def test_load_nonexistent_file_creates_empty_cache(tmp_path: Path):
    """Test behavior with non-existent file."""
    filepath = tmp_path / "missing.json"
    cache = FileCache(filepath, FileFormat.JSON)
    assert cache.data == {}
    assert cache._ready is True

# -----------------------------
# File Format Tests
# -----------------------------
def test_json_write_and_read(tmp_path: Path, sample_data):
    """Test JSON write and read operations."""
    filepath = tmp_path / "test.json"
    cache = FileCache(filepath, FileFormat.JSON)
    
    cache._data = sample_data.copy()
    cache._ready = True
    cache.save()  # No assertion needed, should not raise
    
    new_cache = FileCache(filepath, FileFormat.JSON)
    assert new_cache.data == sample_data

def test_yaml_write_and_read(tmp_path: Path, sample_data):
    """Test YAML write and read operations."""
    filepath = tmp_path / "test.yaml"
    cache = FileCache(filepath, FileFormat.YAML)
    
    cache._data = sample_data.copy()
    cache._ready = True
    cache.save()  # No assertion needed, should not raise
    
    new_cache = FileCache(filepath, FileFormat.YAML)
    assert new_cache.data == sample_data


# -----------------------------
# Write Mode Tests
# -----------------------------
def test_readonly_mode(tmp_path: Path, sample_data):
    """Test read-only mode behavior."""
    filepath = tmp_path / "readonly.json"
    
    # First create file with data
    cache = FileCache(filepath, FileFormat.JSON)
    cache._data = sample_data.copy()
    cache._ready = True
    cache.save()
    
    # Test readonly access
    ro_cache = FileCache(filepath, FileFormat.JSON, FileMode.READONLY)
    assert ro_cache.data == sample_data
    with pytest.raises(RuntimeError, match="cannot be overwritten"):
        ro_cache.save()

def test_atomic_write(tmp_path: Path, sample_data):
    """Test atomic write mode."""
    filepath = tmp_path / "atomic.json"
    cache = FileCache(filepath, FileFormat.JSON, FileMode.ATOMIC_WRITE)
    
    cache._data = sample_data.copy()
    cache._ready = True
    cache.save()  # Should not raise
    
    assert filepath.exists()
    with open(filepath) as f:
        assert json.load(f) == sample_data

def test_secure_write(tmp_path: Path, sample_data):
    """Test secure write mode."""
    filepath = tmp_path / "secure.json"
    cache = FileCache(filepath, FileFormat.JSON, FileMode.SECURE_WRITE)
    
    cache._data = sample_data.copy()
    cache._ready = True
    cache.save()  # Should not raise
    
    assert filepath.exists()
    with open(filepath) as f:
        assert json.load(f) == sample_data



        
# -----------------------------
# Error Handling Tests
# -----------------------------
def test_json_invalid_file_raises(tmp_path: Path):
    """Test handling of invalid JSON file."""
    filepath = tmp_path / "invalid.json"
    filepath.write_text("{ invalid json }")
    
    cache = FileCache(filepath, FileFormat.JSON)
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        _ = cache.data

def test_yaml_invalid_file_raises(tmp_path: Path):
    """Test handling of invalid YAML file."""
    filepath = tmp_path / "invalid.yaml"
    filepath.write_text("{ invalid: yaml: [}")
    
    cache = FileCache(filepath, FileFormat.YAML)
    with pytest.raises(RuntimeError):
        _ = cache.data

def test_write_permission_error(tmp_path: Path):
    """Test handling of write permission errors."""
    filepath = tmp_path / "noperm.json"
    cache = FileCache(filepath, FileFormat.JSON)
    cache._data = {"test": "value"}
    cache._ready = True
    
    with patch('builtins.open', side_effect=PermissionError), \
         pytest.raises(RuntimeError, match="Failed to write file"):
        cache.save()

def test_save_without_ready_raises():
    """Test that saving without ready cache raises ValueError."""
    cache = FileCache(Path("test.json"))
    with pytest.raises(ValueError, match="not properly initialized"):
        cache.save()


# -----------------------------
# Context Manager Tests
# -----------------------------
def test_context_manager(tmp_path: Path, sample_data):
    """Test context manager functionality."""
    filepath = tmp_path / "context.json"
    
    with FileCache(filepath, FileFormat.JSON) as cache:
        cache._data = sample_data.copy()
        cache._ready = True
    
    # Verify file was saved on exit
    assert filepath.exists()
    with open(filepath) as f:
        assert json.load(f) == sample_data

def test_context_manager_with_error(tmp_path: Path):
    """Test context manager error handling."""
    filepath = tmp_path / "context_error.json"
    
    with pytest.raises(ValueError):
        with FileCache(filepath, FileFormat.JSON) as cache:
            raise ValueError("Test error")
    
    # File should not exist since an error occurred
    assert not filepath.exists()