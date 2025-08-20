import pytest
from unittest.mock import MagicMock
import mgconfig.value_stores as vs 


@pytest.fixture
def init_cfg(tmp_path):
    # minimal init config: just the secure store file path
    return {vs.config_securestorefile.config_id: str(tmp_path / "secure.store")}


@pytest.fixture
def dummy_key_provider(monkeypatch):
    class DummyKeyProvider:
        def __init__(self, cfg):
            self.cfg = cfg
    monkeypatch.setattr(vs, "KeyProvider", DummyKeyProvider)
    return DummyKeyProvider


@pytest.fixture
def mock_securestore(monkeypatch):
    """
    Patch vs.SecureStore to return a fresh MagicMock instance per test.
    Expose both the class mock and the instance for assertions.
    """
    cls_mock = MagicMock(name="SecureStoreClassMock")
    inst = MagicMock(name="SecureStoreInstanceMock")
    # reasonable defaults
    inst.validate_master_key.return_value = True
    inst.store_secret.return_value = None
    inst.save.return_value = None
    inst.retrieve_secret.return_value = "secret-value"
    inst.prepare_auto_key_exchange.return_value = "new-master-key"

    cls_mock.return_value = inst
    monkeypatch.setattr(vs, "SecureStore", cls_mock)
    return cls_mock, inst


# -------------------- tests --------------------

def test_init_constructs_secure_store_and_validates(dummy_key_provider, mock_securestore, init_cfg):
    cls_mock, inst = mock_securestore
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    # SecureStore constructed once during __init__
    cls_mock.assert_called_once()
    # constructed with (securestore_file, key_provider)
    args, kwargs = cls_mock.call_args
    assert args[0] == init_cfg[vs.config_securestorefile.config_id]
    assert args[1] is store.key_provider  # exact object passed through

    # validate called
    inst.validate_master_key.assert_called_once()


def test_init_handles_invalid_master_key(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    inst.validate_master_key.return_value = False  # should not raise
    vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)
    inst.validate_master_key.assert_called_once()


def test_save_value_success(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    ok = store.save_value("item1", "topsecret")
    assert ok is True
    # A new SecureStore is created inside save_value()
    assert inst.store_secret.call_args[0] == ("item1", "topsecret")
    inst._ssf_save.assert_called_once()


def test_save_value_failure_raises_path_is_caught(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    inst.store_secret.side_effect = Exception("boom")
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    ok = store.save_value("item1", "x")
    assert ok is False  # error swallowed and logged


def test_retrieve_value_success(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    inst.retrieve_secret.return_value = "s3cr3t"
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    val, src = store.retrieve_value("item1")
    assert val == "s3cr3t"
    assert src == vs.ConfigValueSource.ENCRYPT


def test_retrieve_value_failure_returns_none(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    inst.retrieve_secret.side_effect = Exception("fail")
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    val, src = store.retrieve_value("item1")
    assert val is None
    assert src == vs.ConfigValueSource.ENCRYPT


def test_prepare_new_masterkey_success(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    inst.prepare_auto_key_exchange.return_value = "mk"
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    mk = store.prepare_new_masterkey()
    assert mk == "mk"
    inst.prepare_auto_key_exchange.assert_called_once()


def test_prepare_new_masterkey_failure_returns_none(dummy_key_provider, mock_securestore, init_cfg):
    _, inst = mock_securestore
    inst.prepare_auto_key_exchange.side_effect = Exception("nope")
    store = vs.ValueStoreSecure(cfg_defs={}, init_config=init_cfg)

    mk = store.prepare_new_masterkey()
    assert mk is None
