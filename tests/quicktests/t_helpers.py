# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import shutil
from pathlib import Path
from mgconfig import Configuration, DefaultValues
from mgconfig.secure_store_helpers import generate_key_str


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__test.yml"
]

root_dir = os.path.dirname(os.path.abspath(__file__))
test_basedir = Path(root_dir) / 'temp_basedir'

def prepare_new_env_master_key():
    os.environ["APP_KEY"] = generate_key_str()

def prepare_clean_basedir():
    os.environ["DATA_DIRECTORY"] = test_basedir.as_posix()
    shutil.rmtree(test_basedir, ignore_errors=True)
    test_basedir.mkdir(exist_ok=True)
    return test_basedir


def get_test_filepath(filename):
    return Path(test_basedir) / filename


def create_configuration():
    DefaultValues().clear()
    DefaultValues().add('app_name', 'testapp')
    Configuration.reset_instance()
    return Configuration(CONFIG_DEFINITIONS_YAML)


def remove_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
