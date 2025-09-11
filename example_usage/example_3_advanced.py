# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
from mgconfig import Configuration, DefaultValues, prepare_temp_data_directory, generate_master_key_str


# this function create a new and empty data directory for testing purposes
prepare_temp_data_directory(__file__)


# This environment variable is set to a newly generated key for testing only.
# In real applications, the key should be generated once and then persisted.
# To access the secure store across application runs, reuse the same key instead of regenerating it.
def prepare_initial_master_key() -> None:
    os.environ["APP_KEY"] = generate_master_key_str()


TESTITEMNAME = 'tst_secrets_password'

CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def_2_intermediate.yaml",
    "config_defs/config_def_3_advanced.yaml"
]


# ---------------------------------------------------------------------
# configuration instance creation
# ---------------------------------------------------------------------
config = Configuration(CONFIG_DEFINITIONS_YAML)


# ---------------------------------------------------------------------
# display and change TESTITEM (of config type secret)
# ---------------------------------------------------------------------

print(
    f'Original configuration value for {TESTITEMNAME}: {config.get_value(TESTITEMNAME)}')

# as the config data file (YAML) will not be found in the empty directory, it will be created.
# you can find this file in the basedir after running this example
config.save_new_value(TESTITEMNAME, 'secret test string',
                      apply_immediately=True)

print(
    f'Saved configuration value for {TESTITEMNAME}: {config.get_value(TESTITEMNAME)}')


# ---------------------------------------------------------------------
# test output
# ---------------------------------------------------------------------
key_order = ['config_id', 'config_type',  'readonly_flag', 'config_env',
             'config_default', 'source_str',  'value_str']
for row in config.data_rows:
    print([row[k] for k in key_order])
