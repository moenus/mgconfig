# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


# ------------------------------------------------------------------------------------------------------------
# ConfigKeyMap
# ------------------------------------------------------------------------------------------------------------

APP = 'app'
SEC = 'sec'


class ConfigKeyMap:
    """Represents a predefined configuration key (singleton) with remapping support.

    Each `(section_prefix, config_name)` pair corresponds initially to exactly one
    `ConfigKeyMap` instance. Subsequent calls with the same pair return
    the already existing instance from the registry.

    The object has two notions of identity:

    - `_registry_key`: Immutable identifier assigned at creation
      (``"<section_prefix>_<config_name>"``). Used for singleton uniqueness
      and registry membership.
    - `id`: Dynamic identifier, always computed from the current values of
      :attr:`section_prefix` and :attr:`config_name`. This may differ from
      `_registry_key` if the object has been remapped.

    Attributes:
        section_prefix (str): Prefix for the configuration section (mutable).
        config_name (str): Identifier for the configuration entry within a section (mutable).
        _registry_key (str): Immutable key assigned at creation time,
            in the form ``"<section_prefix>_<config_name>"``.
    """
    _registry: dict[str, "ConfigKeyMap"] = {}  # name -> instance

    def __new__(cls, section_prefix: str, config_name: str, *args, **kwargs):
        """Create or return a singleton instance for the given configuration key.

        Args:
            section_prefix (str): Prefix for the configuration section (e.g., "app").
            config_name (str): Identifier for the configuration entry within a section.

        Returns:
            ConfigKeyMap: Existing or newly created instance associated with
            the registry key ``"<section_prefix>_<config_name>"``.
        """
        key = f'{section_prefix}_{config_name}'
        if key in cls._registry:
            return cls._registry[key]  # return existing instance
        instance = super().__new__(cls)
        cls._registry[key] = instance
        return instance

    def __init__(self, section_prefix: str,  config_name: str) -> None:
        """Initialize the configuration key instance.

        This initializer runs only once per unique `(section_prefix, config_name)`
        pair. Subsequent instantiations return the existing object.

        Args:
            section_prefix (str): Prefix for the configuration section (e.g., "app").
            config_name (str): Identifier for the configuration entry within a section.
        """
        # Prevent reinitialization if instance already exists
        if not hasattr(self, "_initialized"):
            self._registry_key = f'{section_prefix}_{config_name}'
            # can be changed later without changing _config_handle
            self.config_name = config_name
            self.section_prefix = section_prefix  # can be changed later
            self._initialized = True

    @property
    def id(self) -> str:
        """Current configuration identifier.

        Returns:
            str: Composite identifier in the form
            ``"<section_prefix>_<config_name>"`` reflecting the latest values.
        """
        return f'{self.section_prefix}_{self.config_name}'

    def __str__(self) -> str:
        """Return the original registry key as a string."""
        return self._registry_key

    def __repr__(self) -> str:
        """Return a debug representation of the object."""        
        return f'{self._registry_key} --> {self.id}'    

    @classmethod
    def list_registry_keys(cls) -> list[str]:
        """List all original registry keys.

        Returns:
            list[str]: List of immutable registry keys (frozen at creation).
        """
        return [item._registry_key for item in cls._registry.values()]

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered configuration keys (useful for testing)."""
        cls._registry.clear()