# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

# test_mgconf.py
import logging
import pytest
from mgconfig.config_logger import LoggerWrapper


# -------------------------
# Tests for LoggerWrapper
# -------------------------
def test_loggerwrapper_default_logger(monkeypatch):
    lw = LoggerWrapper()
    assert isinstance(lw._logger, logging.Logger)
    # Test delegation
    assert hasattr(lw, "debug")
    assert callable(lw.debug)

def test_loggerwrapper_replace_logger():
    lw = LoggerWrapper()
    new_logger = logging.getLogger("NEW_LOGGER")
    lw.replace_logger(new_logger)
    assert lw._logger is new_logger

    # Replacing with non-logger raises
    with pytest.raises(TypeError):
        lw.replace_logger("not_a_logger")
