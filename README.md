# mgconfig  
_A lightweight, declarative configuration system for Python applications_

[![PyPI version](https://badge.fury.io/py/mgconfig.svg)](https://pypi.org/project/mgconfig/)  
[![Python Versions](https://img.shields.io/pypi/pyversions/mgconfig.svg)](https://pypi.org/project/mgconfig/)  
[![Docs Status](https://readthedocs.org/projects/mgconfig/badge/?version=latest)](https://mgconfig.readthedocs.io/en/latest/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
---

## Features

- 📝 **Declarative configuration** — define schemas in YAML with explicit types, defaults, and namespaces  
- 🔄 **Dynamic values** — function-based defaults, environment variable overrides, and runtime-resolved values (e.g. timestamps, system info)  
- 🔐 **Secret management** — encrypted storage of sensitive values, multiple master key storage options, and key rotation support  
- ⚙️ **Extensible API** — programmatic access, custom converters, and support for unit testing  

---

## Why Choose mgconfig?

- **Schema-first design** — configuration structure and types are declared in YAML, keeping definitions consistent and centralized  
- **Environment-aware** — values can be overridden by environment variables without changing the YAML files  
- **Built-in security** — supports encryption, salting, secure key storage (environment, keyring, or file), and key rotation  
- **Gradual learning curve** — documentation includes basic, intermediate, and advanced examples  
- **Transparent limitations** — known caveats are documented so users can make informed decisions  
- **Customizable** — easy to add new converters or integrate with existing frameworks  


---

## Quick Start

### Installation
```bash
pip install mgconfig
```

### Configuration Definition (config_def.yaml)

```yaml
- section: application
  prefix: app
  configs:

  - name: configfile
    type: path
    default: config.yaml

  - name: test
    type: str
    default: teststring

  - name: timeout
    type: int
    default: 30    
```

### Configuration Values (config.yaml)

```yaml
app:
  timeout: 55
```

### Basic Usage Example
⚠️ ⚠️ Values are accessed using the defined prefix (e.g. app) plus an underscore and the config name (e.g. app_test, app_timeout).

```python
from mgconfig import Configuration

# Load schema definition and configuration values
# configuration values will be loaded from defaults or config.yaml in this example
config = Configuration("config_def.yaml")

# Access configuration values
print(config.get_value("app_test"))     # -> "teststring"
print(config.get_value("app_timeout"))  # -> 55
```


## Documentation

📖 Learn more:

- [User Guide](https://mgconfig.readthedocs.io/en/latest) — overview and full documentation
- [API Reference](https://mgconfig.readthedocs.io/en/latest/doc_api.html) — API syntax description
- [Configuration Definition](https://mgconfig.readthedocs.io/en/latest/doc_config_definition.html) —  file syntax, options and examples

## Requirements

- Python 3.7+ 
- [tzlocal](https://pypi.org/project/tzlocal/)
- [PyYAML](https://pypi.org/project/PyYAML/)
- [keyring](https://pypi.org/project/keyring/) (optional, for master key storage)

## Known Limitations

See the [Known Bugs and Limitations](https://mgconfig.readthedocs.io/en/latest/doc_known_bugs_and_limitations.html) section in the documentation for current issues and caveats.

## Security Considerations

mgconfig can securely store and manage sensitive configuration values. Make sure to review the security documentation for:

- salting support,
- master key storage options (environment, keyring, protected files),
- lifecycle and key rotation. 

See the [Security Considerations](https://mgconfig.readthedocs.io/en/latest/doc_secure_store.html) section in the documentation for more information on the usage of secure storage.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.



