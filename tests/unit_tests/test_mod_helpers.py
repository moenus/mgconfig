import unittest
import logging
from unittest.mock import Mock
from mgconfig.helpers import (
    ConfigKeyMap,
    LoggerWrapper,
)



class TestLoggerWrapper(unittest.TestCase):
    def test_default_logger(self):
        lw = LoggerWrapper()
        self.assertTrue(hasattr(lw._logger, "debug"))

    def test_replace_logger(self):
        lw = LoggerWrapper()
        new_logger = logging.getLogger("test_logger")
        lw.replace_logger(new_logger)
        # Now the internal logger should be replaced
        self.assertIs(lw._logger, new_logger)

    def test_replace_logger_type_error(self):
        lw = LoggerWrapper()
        with self.assertRaises(TypeError):
            lw.replace_logger("not a logger")
