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
- Programmatic API for changing configuration settings
- Extensible with custom defaults, default functions, custom types, etc.

.. _config_types:

Configuration Types
~~~~~~~~~~~~~~~~~~~
The following configuration types are available in the mgconfig package:

['str', 'int', 'float', 'bool', 'date', 'time', 'path', 'secret', 'bytes', 'hidden']


Additional configuration types can be implemented.

See section :doc:`examples/doc_example_4_extended` for an example how to do add the following types:

['minutes', 'seconds', 'filename']


