from typing import Callable, Optional, Any
from types import MappingProxyType


class DefaultsDict:
    _instance = None

    def __new__(cls):
        # Name-mangled, so private to each class
        private_instance_name = f"_{cls.__name__}__instance"

        if not hasattr(cls, private_instance_name):
            instance = super().__new__(cls)
            instance.defaults = {}
            setattr(cls, private_instance_name, instance)

        return getattr(cls, private_instance_name)

    def add(self, name, value):
        self.defaults[name] = value

    def get(self, name):
        return self.defaults.get(name)

    def clear(self):
        self.defaults.clear()

    def contains(self, name):
        return name in self.defaults

    @property
    def dict(self):
        return MappingProxyType(self.defaults)


class DefaultValues(DefaultsDict):
    pass


class DefaultFunctions(DefaultsDict):
    def add(self, name, value: Callable):
        if callable(value):
            self.defaults[name] = value
        else:
            raise ValueError('Value is not callable.')


class PostProcessing(DefaultsDict):
    def add(self, func_value: Callable):
        if callable(func_value):
            self.defaults[func_value.__name__] = func_value
        else:
            raise ValueError('Value is not callable.')

# test = DefaultValues()
# test.add('abd', 'xyz')
# print(test.get('abd'))
# DefaultValues().add('a12', 'b13')
# print(test.get('a12'))
# print(test.dict)


default_values_obj = DefaultValues()         # creation of singleton object
default_functions_obj = DefaultFunctions()   # creation of singleton object
