# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig import Configuration, ConfigTypes, DefaultValues


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__example.yml"
]

# # ---------------------------------------------------------------------
# # default values - example
# # ---------------------------------------------------------------------
DefaultValues().clear()
DefaultValues().add('app_name', 'appname')

# ---------------------------------------------------------------------
# configuration item value creation
# ---------------------------------------------------------------------
config = Configuration(CONFIG_DEFINITIONS_YAML)

# ---------------------------------------------------------------------
# test output
# ---------------------------------------------------------------------
print(ConfigTypes.list_all())
for row in config.data_rows:
    print(row)