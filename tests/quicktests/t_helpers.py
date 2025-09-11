# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from mgconfig import Configuration, DefaultValues, generate_master_key_str, prepare_temp_data_directory, internal_reset


def prepare_new_env_master_key():
    os.environ["APP_KEY"] = generate_master_key_str()

CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__test.yml"
]

def prepare_clean_basedir():
    return prepare_temp_data_directory(__file__)

test_basedir = prepare_clean_basedir()


def get_test_filepath(filename):
    return Path(test_basedir) / filename

def remove_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


def create_configuration():
    internal_reset()
    DefaultValues().add('app_name', 'testapp')
    return Configuration(CONFIG_DEFINITIONS_YAML)
