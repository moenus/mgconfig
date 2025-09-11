# Python Package mgconfig

**mgconfig** is a lightweight Python configuration system driven by declarative YAML definitions.  
### Features

- Declarative YAML configuration schema
- Default values (static or dynamic via functions)
- Programmatic defaults for application metadata
- Environment variable overrides
- Strongly typed parsing, validation, and display
- Hierarchical sections and namespace prefixes for avoiding collisions
- Programmatic API for setting defaults
- Extensible with custom default functions

---

## Installation

```bash
# From source (assuming you're in the repository root)
pip install -e .

# Or install runtime dependencies if not using an editable install
pip install tzlocal 

``` 
---


## Dependencies
- tzlocal — for determining the local timezone

Python 3.7+ recommended

## License

This project is licensed under the MIT License.

## Documentation

Full documentation is available at: https://mgconfig.readthedocs.io


# mgconfig

A lightweight, declarative configuration system for Python applications with secure key storage.

[![PyPI version](https://badge.fury.io/py/mgconfig.svg)](https://badge.fury.io/py/mgconfig)
[![Python Versions](https://img.shields.io/pypi/pyversions/mgconfig.svg)](https://pypi.org/project/mgconfig/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔐 **Secure Key Storage**
  - Support for environment variables, keyring, and encrypted files
  - Automatic sensitive data protection
  - Master key management

- 📝 **Declarative Configuration**
  - YAML-based schema definitions
  - Type validation and conversion
  - Hierarchical sections with namespaces

- 🔄 **Dynamic Values**
  - Function-based default values
  - Environment variable overrides
  - Application metadata integration

- 🛠️ **Developer Friendly**
  - Programmatic API
  - Extensible architecture
  - Comprehensive testing support

## Quick Start

### Installation

```bash
pip install mgconfig
```

### Basic Usage

```python
from mgconfig import ConfigDef, SEC

# Define configuration
app_config = [
    ConfigDef(SEC.APP, "name", default="MyApp"),
    ConfigDef(SEC.APP, "debug", type_hint="bool", default="false"),
    ConfigDef(SEC.DB, "password", is_secret=True)
]

# Load and use configuration
config.load("config.yaml", app_config)
app_name = config.get_value("app.name")
```

### Configuration File (config.yaml)

```yaml
app:
  name: CustomApp
  debug: true
db:
  host: localhost
  password: ${DB_PASSWORD}  # Read from environment
```

## Advanced Features

### Secure Key Storage

```python
from mgconfig import KeyStores

# Store sensitive data
KeyStores.set_key("keyring", "db.password", "secret123")

# Retrieve securely
password = KeyStores.get_key("keyring", "db.password")
```

### Custom Default Providers

```python
from mgconfig import register_default_provider

@register_default_provider("hostname")
def get_hostname():
    return socket.gethostname()
```

## Documentation

For detailed documentation, visit:
- [User Guide](https://mgconfig.readthedocs.io/en/latest/guide/)
- [API Reference](https://mgconfig.readthedocs.io/en/latest/api/)
- [Security](https://mgconfig.readthedocs.io/en/latest/security/)

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/mgconfig.git
cd mgconfig

# Set up development environment
python -m venv venv
.\venv\Scripts\activate
pip install -e ".[dev]"

# Run tests
pytest
```

## Requirements

- Python 3.7+
- tzlocal
- pyyaml
- keyring (optional, for secure storage)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.