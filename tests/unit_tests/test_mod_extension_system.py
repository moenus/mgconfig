# test_defaults_dict.py
import pytest
from types import MappingProxyType
from mgconfig.extension_system import DefaultValues, DefaultFunctions, PostProcessing


def test_singleton_behavior():
    """Ensure that each class is a singleton."""
    v1 = DefaultValues()
    v2 = DefaultValues()
    f1 = DefaultFunctions()
    f2 = DefaultFunctions()
    p1 = PostProcessing()
    p2 = PostProcessing()
    
    assert v1 is v2
    assert f1 is f2
    assert p1 is p2


def test_add_and_get_values():
    """Test adding and retrieving values."""
    dv = DefaultValues()
    dv.clear()
    
    dv.add("key1", 123)
    dv.add("key2", "value")
    
    assert dv.get("key1") == 123
    assert dv.get("key2") == "value"
    assert dv.get("missing") is None
    assert dv.contains("key1") is True
    assert dv.contains("missing") is False


def test_add_duplicate_raises():
    """Adding a duplicate key should raise KeyError."""
    dv = DefaultValues()
    dv.clear()
    dv.add("key", 42)
    
    with pytest.raises(KeyError):
        dv.add("key", 100)


def test_dict_immutable():
    """The .dict property should return an immutable mapping."""
    dv = DefaultValues()
    dv.clear()
    dv.add("a", 1)
    
    d = dv.dict
    assert isinstance(d, MappingProxyType)
    with pytest.raises(TypeError):
        d["b"] = 2


def test_default_functions_add_callable():
    """Test that DefaultFunctions only accepts callables."""
    df = DefaultFunctions()
    df.clear()
    
    def func(): return 1
    df.add("func1", func)
    
    assert df.get("func1")() == 1
    
    with pytest.raises(ValueError):
        df.add("not_callable", 123)


def test_postprocessing_add_callable():
    """Test that PostProcessing stores functions by name."""
    pp = PostProcessing()
    pp.clear()
    
    def sample_func(): return "ok"
    
    pp.add(sample_func)
    
    # Check stored by function name
    assert pp.get("sample_func")() == "ok"
    
    with pytest.raises(ValueError):
        pp.add("not_callable")


def test_clear_method():
    """Test that clear empties the dictionary."""
    dv = DefaultValues()
    dv.clear()
    dv.add("x", 10)
    
    assert dv.contains("x")
    dv.clear()
    assert not dv.contains("x")
    assert dv.dict == {}


def test_combined_usage():
    """Test that different singletons don't interfere."""
    dv = DefaultValues()
    df = DefaultFunctions()
    pp = PostProcessing()
    
    dv.clear()
    df.clear()
    pp.clear()
    
    dv.add("val", 5)
    df.add("func", lambda: 10)
    
    def post(): return "done"
    pp.add(post)
    
    assert dv.get("val") == 5
    assert df.get("func")() == 10
    assert pp.get("post")() == "done"
