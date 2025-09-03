import os
import json
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock

from mgconfig import keystores
from mgconfig.keystores import (
    KeyStore, KeyStoreFile, KeyStoreKeyring, KeyStoreEnv, KeyStores
)


# -----------------------------
# Base KeyStore
# -----------------------------
def test_keystore_set_raises():
    ks = KeyStore()
    with pytest.raises(ValueError):
        ks.set("foo", "bar")


def test_get_param_and_missing():
    ks = KeyStore()
    ks.params = {"foo": "bar"}
    assert ks.get_param("foo") == "bar"
    with pytest.raises(ValueError):
        ks.get_param("missing")


def test_check_configuration_unconfigured():
    ks = KeyStore()
    with pytest.raises(ValueError):
        ks.check_configuration()


# -----------------------------
# KeyStoreEnv
# -----------------------------
def test_env_get(monkeypatch):
    monkeypatch.setenv("MYVAR", "123")
    ks = KeyStoreEnv()
    assert ks.get("MYVAR") == "123"
    assert ks.get("MISSING") is None


# -----------------------------
# KeyStores registry
# -----------------------------
def test_add_and_get_contains():
    ks = KeyStore()
    ks.keystore_name = "custom"

    # Ensure fresh registry
    KeyStores._ks_dict = {}
    KeyStores.add(ks)

    assert KeyStores.contains("custom")
    assert KeyStores.get("custom") == ks

    with pytest.raises(ValueError):
        KeyStores.add(ks)
