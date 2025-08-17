# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

Introduction
============

**mgconfig** is a lightweight Python configuration system driven by declarative YAML definitions.  

Features
~~~~~~~~
- Declarative YAML configuration schema
- Default values (static or dynamic via functions)
- Programmatic defaults for application metadata
- Environment variable overrides
- Strongly typed parsing, validation, and display
- Hierarchical sections and namespace prefixes for avoiding collisions
- Programmatic API for setting defaults
- Extensible with custom default functions

.. _config_types:

Configuration Types
~~~~~~~~~~~~~~~~~~~
The following configuration types are available in the mgconfig package:

['str', 'int', 'float', 'bool', 'date', 'time', 'path', 'secret', 'bytes', 'hidden']


Additional configuration types can be implemented by using the mechanisms described in the example_usage.py which adds the following types:

['minutes', 'seconds', 'filename']



Known Bugs and Limitations
==========================

- ``None`` type is used for missing values. 

  Therefore setting a value to ``None`` will delete this value from the ``configuration file`` respectively from the ``securestore file``. A default cannot be overwritten with ``None`` from a higher priority source. 
  A value can only be None, if there is no default and the value was not set in the environment variables or one of the above mentiioned files. 

- The package is not thread-safe.

  As configuration values should be determined only once at application startup and setting values is assumed to happen not verry often, this might be acceptable for most use cases. 
  If you need thread-safety it needs to be applied as a wrapper around the used mgconfig objects. 
