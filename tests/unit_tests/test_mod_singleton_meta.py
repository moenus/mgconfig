# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import unittest
from mgconfig.singleton_meta import SingletonMeta

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
