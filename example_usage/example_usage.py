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
key_order = ['config_id', 'config_type',  'readonly_flag', 'config_env',
             'config_default', 'source_str',  'value_str']
for row in config.data_rows:
    print([row[k] for k in key_order])
