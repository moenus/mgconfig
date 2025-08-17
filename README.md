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
