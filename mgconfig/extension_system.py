# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from typing import Callable, Any, Optional, Dict
from types import MappingProxyType
from abc import ABC


class DefaultsDict(ABC):
    """
    Base class for a singleton dictionary that stores default values or functions.

    This class ensures only one instance exists per subclass.
    Provides methods to add, get, clear, and check for items.
    """
    def __new__(cls) -> "DefaultsDict":
        """
        Create or return the singleton instance of the class.

        Returns:
            DefaultsDict: The singleton instance of the subclass.
        """
        # Name-mangled, so private to each class
        private_instance_name = f"_{cls.__name__}__instance"

        if not hasattr(cls, private_instance_name):
            instance = super().__new__(cls)
            instance.defaults = {}
            setattr(cls, private_instance_name, instance)

        return getattr(cls, private_instance_name)

    def add(self, name: str, value: Any) -> None:
        """
        Add a new default value to the dictionary.

        Args:
            name (str): The key under which to store the value.
            value (Any): The value to store.

        Raises:
            KeyError: If the key already exists.
        """
        if name in self.defaults:
            raise KeyError(f"'{name}' already exists.")
        self.defaults[name] = value

    def get(self, name: str) -> Optional[Any]:
        """
        Retrieve a value from the dictionary.

        Args:
            name (str): The key of the value to retrieve.

        Returns:
            Any | None: The value if it exists, otherwise None.
        """
        return self.defaults.get(name)

    def clear(self) -> None:
        """
        Clear all items from the dictionary.
        """
        self.defaults.clear()

    def contains(self, name: str) -> bool:
        """
        Check if a key exists in the dictionary.

        Args:
            name (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return name in self.defaults

    @property
    def dict(self) -> Dict[str, Any]:
        """
        Get a read-only view of the dictionary.

        Returns:
            MappingProxyType: An immutable mapping of the stored items.
        """
        return MappingProxyType(self.defaults)


class DefaultValues(DefaultsDict):
    """
    Singleton dictionary for storing default values.
    """
    pass


class DefaultFunctions(DefaultsDict):
    """
    Singleton dictionary for storing default callable functions.
    """

    def add(self, name: str, value: Callable) -> None:
        """
        Add a callable function to the dictionary.

        Args:
            name (str): The key under which to store the function.
            value (Callable): The function to store.

        Raises:
            ValueError: If the provided value is not callable.
        """
        if not callable(value):
            raise ValueError('Value is not callable.')
        super().add(name, value)


class PostProcessing(DefaultsDict):
    """
    Singleton dictionary for storing post-processing functions.
    The function name is used as the key.
    """

    def add(self, func_value: Callable) -> None:
        """
        Add a post-processing function to the dictionary.

        Args:
            func_value (Callable): The function to store.

        Raises:
            ValueError: If the provided value is not callable.
        """
        if not callable(func_value):
            raise ValueError('Value is not callable.')
        super().add(func_value.__name__, func_value)


# Creation of singleton objects
default_values_obj: DefaultValues = DefaultValues()
default_functions_obj: DefaultFunctions = DefaultFunctions()
