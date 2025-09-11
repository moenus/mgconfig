Configuration Definition
========================

`mgconfig` is driven by YAML **configuration definition** files.  
They do **not** directly store runtime values — instead, they describe:

- **Sections**: logical groups of related settings.
- **Prefixes**: short identifiers prepended to config names for namespacing.
- **Configs**: individual configuration items, each with:
    - **name** — short key for the setting.
    - **type** — one of the supported types (see :ref:`config_types`).
    - **readonly** — marks a config as “readonly". (No changes to the values are allowed)
    - **description** — human-readable explanation.
    - **default** — static default value (supports references to other configs via `$(...)`).
    - **env** — environment variable name for overrides.
    - **default_function** — name of a registered Python function to supply a dynamic default.


See :doc:`examples/index` for examples of ``Configuration Definition Files``
