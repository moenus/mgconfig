import unittest
import logging
from unittest.mock import Mock
from mgconfig.helpers import (
    ConfigKeyMap,
    LoggerWrapper,
    SingletonMeta,
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

class TestSingletonMeta(unittest.TestCase):
    def setUp(self):
        SingletonMeta._instances.clear()

    def test_singleton_behavior(self):
        class MySingleton(metaclass=SingletonMeta):
            def __init__(self, value):
                self.value = value

        s1 = MySingleton(10)
        s2 = MySingleton(20)
        self.assertIs(s1, s2)
        self.assertEqual(s1.value, 10)

    def test_reset_instance(self):
        class MySingleton(metaclass=SingletonMeta):
            def __init__(self, value):
                self.value = value

        s1 = MySingleton(1)
        MySingleton.reset_instance()
        s2 = MySingleton(2)
        self.assertIsNot(s1, s2)
        self.assertEqual(s2.value, 2)

if __name__ == "__main__":
    unittest.main()
