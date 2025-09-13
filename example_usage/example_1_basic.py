# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

# import from mgconfig
from mgconfig import Configuration

# configuration object creation
config = Configuration('config_defs/config_def_1_basic.yaml')

# access configuration value
print(f"Test configuration value: {config.app_test}")