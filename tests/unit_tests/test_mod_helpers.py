import unittest
import logging
from unittest.mock import Mock
from mgconfig.helpers import (
    ConstSection,
    ConstConfig,
    Section,
    lazy_build_config_id,
    LoggerWrapper,
    SingletonMeta,
)

class TestConstSection(unittest.TestCase):
    def setUp(self):
        # Clear the registry before each test
        ConstSection._registry.clear()

    def test_singleton_behavior(self):
        s1 = ConstSection("APP", "app")
        s2 = ConstSection("APP", "app2")
        self.assertIs(s1, s2)
        self.assertEqual(s1.section_prefix, "app")

    def test_section_prefix_property(self):
        s = ConstSection("SEC", "sec")
        self.assertEqual(s.section_prefix, "sec")
        s.section_prefix = "new_sec"
        self.assertEqual(s.section_prefix, "new_sec")

    def test_section_prefix_undefined_raises(self):
        s = ConstSection("NEW")
        with self.assertRaises(ValueError):
            _ = s.section_prefix

    def test_list_handles(self):
        ConstSection("A", "a")
        ConstSection("B", "b")
        self.assertListEqual(sorted(ConstSection.list_handles()), ["A", "B"])

class TestConstConfig(unittest.TestCase):
    def setUp(self):
        ConstConfig._registry.clear()
        self.section = ConstSection("APP", "app")

    def test_singleton_behavior(self):
        c1 = ConstConfig("configfile", self.section)
        c2 = ConstConfig("configfile", self.section)
        self.assertIs(c1, c2)

    def test_config_id_lazy_build(self):
        c = ConstConfig("configfile", self.section)
        self.assertEqual(c.config_id, "app_configfile")
        c.config_id = "custom_id"
        self.assertEqual(c.config_id, "custom_id")

    def test_list_handles(self):
        ConstConfig("c1", self.section)
        ConstConfig("c2", self.section)
        self.assertListEqual(sorted(ConstConfig.list_handles()), ["c1", "c2"])

class TestLazyBuildConfigID(unittest.TestCase):
    def test_lazy_build_config_id(self):
        section = ConstSection("APP", "app")
        result = lazy_build_config_id(section, "configfile")
        self.assertEqual(result, "app_configfile")

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
