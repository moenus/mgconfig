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

Configuration definition file example
-------------------------------------

Example for a YAML configuration definition file::

      - section: application
        prefix: app
        configs:

          - name: name
            type: str
            readonly: True
            description: name of the application (read only)

          - name: basedir
            type: path
            readonly: True
            default: /$(app_name)_data
            env: DATA_DIRECTORY
            description: base directory for application execution

          - name: configdir
            type: path
            readonly: True
            default: $(app_basedir)/configs
            env: CONFIG_DIRECTORY
            description: configuration directory (read only)

          - name: configfile
            type: path
            readonly: True
            default: $(app_configdir)/$(app_name)_config.yaml
            env: CONFIGFILE
            description: full pathname of configuration file (read only)

      - section: secure_store
        prefix: sec
        configs:

          - name: securestore_file
            type: path
            readonly: True
            default: '$(app_configdir)/$(app_name)_sec.json'
            env: SECURESTORE_FILE
            description: filepath of secure store file
