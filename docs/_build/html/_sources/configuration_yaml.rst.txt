## Configuration YAML Overview

`mgconfig` is driven by a YAML configuration **definition** file.  
It does **not** directly store runtime values — instead, it describes:

- **Sections**: logical groups of related settings.
- **Prefixes**: short identifiers prepended to config names for namespacing.
- **Configs**: individual configuration items, each with:
  - **name** — short key for the setting.
  - **type** — one of the supported types (e.g., `str`, `int`, `bool`, `path`, `base64`, `seconds`, `minutes`, `time`, `secret`, `fn`).
  - **basic** — marks a config as “core” or “simple”.
  - **description** — human-readable explanation.
  - **default** — static default value (supports references to other configs via `$(...)`).
  - **env** — environment variable name for overrides.
  - **default_function** — name of a registered Python function to supply a dynamic default.

### Minimal working example

```yaml
- section: application
  prefix: app
  configs:

  - name: title
    type: str
    basic: True
    description: full title of the application (shown in web UI) (read only)

  - name: name
    type: str
    basic: True
    description: name of the application (read only)

  - name: version
    type: str
    basic: True
    description: version of the application (read only)

  - name: prefix
    type: str
    basic: True
    description: abbreviation for the application which is used for URLs, file names, etc. (read only)

  - name: basedir
    type: path
    basic: True
    default: /$(app_name)_data
    env: DATA_DIRECTORY
    description: base directory for application execution

  - name: configdir
    type: path
    basic: True
    default: $(app_basedir)/configs
    env: CONFIG_DIRECTORY
    description: configuration directory (read only)

  - name: configfile
    type: path
    basic: True
    default: $(app_configdir)/$(app_name)_config.yaml
    env: CONFIGFILE
    description: full pathname of configuration file (read only)

  - name: key
