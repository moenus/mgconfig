# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import threading

# ------------------------------------------------------------------------------------------------------------
# SingletonMeta
# ------------------------------------------------------------------------------------------------------------


class SingletonMeta(type):
    """Thread-safe metaclass for implementing the Singleton pattern."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Return the singleton instance, creating it if necessary.

        Args:
            *args: Positional arguments for instance initialization.
            **kwargs: Keyword arguments for instance initialization.

        Returns:
            object: Singleton instance of the class.
        """
        # attach a per-class lock lazily
        lock = getattr(cls, "_lock", None)
        if lock is None:
            lock = threading.RLock()
            setattr(cls, "_lock", lock)

        if cls in SingletonMeta._instances:
            instance = SingletonMeta._instances[cls]
            return instance

        with lock:
            # double-check inside lock
            if cls in SingletonMeta._instances:
                return SingletonMeta._instances[cls]

            instance = cls.__new__(cls, *args, **kwargs)
            instance._initialized = False
            cls.__init__(instance, *args, **kwargs)

            SingletonMeta._instances[cls] = instance
            return instance

    def reset_instance(cls) -> None:
        """Reset the singleton instance for this class.

        Removes the instance from the registry, so a new one will be created
        on the next instantiation.
        """
        lock = getattr(cls, "_lock", None)
        if lock is None:
            return
        with lock:
            if cls in SingletonMeta._instances:
                del SingletonMeta._instances[cls]
            # also remove the lock
            if hasattr(cls, "_lock"):
                delattr(cls, "_lock")
