# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig import Configuration, prepare_temp_data_directory

# this function create a new and empty data directory for testing purposes
prepare_temp_data_directory(__file__)


TESTITEMNAME = 'tst_name'

# ---------------------------------------------------------------------
# configuration instance creation
# ---------------------------------------------------------------------
config = Configuration("config_defs/config_def_2_intermediate.yaml")

print(f"Test configuration value for app_name: {config.app_name}")
print(f"Test configuration value for app_basedir: {config.app_basedir}")


# ---------------------------------------------------------------------
# display and change TESTITEM (of config type str)
# ---------------------------------------------------------------------

print(
    f'Original configuration value for {TESTITEMNAME}: {config.get_value(TESTITEMNAME)}')

# as the config data file (YAML) will not be found in the empty directory, it will be created.
# you can find this file in the basedir after running this example
config.save_new_value(TESTITEMNAME, 'new string', apply_immediately=True)

print(
    f'Saved configuration value for {TESTITEMNAME}: {config.get_value(TESTITEMNAME)}')
