import json
import yaml
import pytest
from pathlib import Path
from mgconfig.file_cache import FileCache, FileFormat


def test_load_nonexistent_file_creates_empty_cache(tmp_path: Path):
    filepath = tmp_path / "missing.json"
    cache = FileCache(filepath, FileFormat.JSON)

    assert cache.data == {}  # should be empty dict
    assert cache._ready is True


def test_json_write_and_read(tmp_path: Path):
    filepath = tmp_path / "test.json"
    cache = FileCache(filepath, FileFormat.JSON)

    cache.data["foo"] = "bar"
    assert cache.save() is True

    # reload new instance from same file
    new_cache = FileCache(filepath, FileFormat.JSON)
    assert new_cache.data["foo"] == "bar"


def test_yaml_write_and_read(tmp_path: Path):
    filepath = tmp_path / "test.yaml"
    cache = FileCache(filepath, FileFormat.YAML)

    cache.data["alpha"] = 123
    cache.data["beta"] = [1, 2, 3]
    assert cache.save() is True

    # reload new instance
    new_cache = FileCache(filepath, FileFormat.YAML)
    assert new_cache.data["alpha"] == 123
    assert new_cache.data["beta"] == [1, 2, 3]


def test_clear_resets_cache(tmp_path: Path):
    filepath = tmp_path / "test.json"
    cache = FileCache(filepath, FileFormat.JSON)
    cache.data["key"] = "value"
    cache.clear()

    assert cache._data == {}
    assert cache._ready is False


def test_invalid_extension_raises(tmp_path: Path):
    filepath = tmp_path / "test.txt"
    with pytest.raises(ValueError):
        FileCache(filepath)



def test_save_without_prepare_raises(tmp_path: Path):
    """Test that saving without preparing the cache raises ValueError."""
    filepath = tmp_path / "test.json"
    cache = FileCache(filepath, FileFormat.JSON)
    # Never touched cache.data, so not _ready
    with pytest.raises(ValueError, match="Cannot save"):
        cache.save()


def test_yaml_empty_file_returns_empty_dict(tmp_path: Path):
    filepath = tmp_path / "empty.yaml"
    filepath.write_text("")  # empty file

    cache = FileCache(filepath, FileFormat.YAML)
    assert cache.data == {}  # safe_load returns None, converted to {}


def test_json_invalid_file_raises(tmp_path: Path):
    filepath = tmp_path / "bad.json"
    filepath.write_text("{ invalid json }")

    cache = FileCache(filepath, FileFormat.JSON)
    with pytest.raises(RuntimeError):
        _ = cache.data
