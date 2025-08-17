Usage
=====

This guide shows how to use the **mgconfig** package in your project.

Basic Example
-------------

Import the configuration module and load a configuration file:

.. code-block:: python

    from mgconfig.configuration import Config

    # Load configuration from a file
    config = Config("settings.yaml")

    # Access configuration values
    db_host = config.get("database.host")
    print(f"Database host: {db_host}")


Advanced Usage
--------------

- **Overriding configuration** from environment variables
- **Merging multiple configuration files**
- **Validating configuration** before use

Example with environment override:

.. code-block:: python

    import os
    from mgconfig.configuration import Config

    os.environ["DATABASE_HOST"] = "localhost"
    config = Config("settings.yaml", env_prefix="DATABASE_")

    print(config.get("host"))

Further Reading
---------------

See the :doc:`api` section for the full API reference.
