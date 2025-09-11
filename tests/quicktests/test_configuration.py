# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from datetime import time
from pathlib import Path
from tests.quicktests.t_helpers import prepare_clean_basedir, create_configuration, prepare_new_env_master_key
from mgconfig.config_items import config_items, config_items_new


BASE_DIRECTORY_PATH = prepare_clean_basedir()

test_values = {
    'app_name': 'testapp',
    'app_basedir': BASE_DIRECTORY_PATH,
    'tst_string': 'teststring',
    'tst_integer': 999,
    'tst_bool': True,
    'tst_time': time(14, 30),
    'tst_path': Path(r'\dir\a.txt')
}

new_values = {
    'tst_string': 'newstring',
    'tst_integer': 500,
    'tst_bool': False,
    'tst_time': time(9, 11, 25),
    'tst_path': Path(r'\dir\b.txt'),
    # 'tst_secret': 'newpw'
}

new_values_immediate = {
    'tst_string': 'newstring_immediate',
    'tst_integer': 600,
    'tst_bool': True,
    'tst_time': time(13, 11, 25),
    'tst_path': Path(r'\dir\c.txt'),
    # 'tst_secret': 'geheim'
}

new_values_immediate_ext = {
    'tst_path': Path(r'\dir\c.txt'),
}


def test_configuration_reading():
    prepare_clean_basedir()
    prepare_new_env_master_key()
    config = create_configuration()

    assert config.app_name == test_values['app_name']

    for key, value in test_values.items():
        assert config.get_value(key) == value

    for config_value in config_items.values():
        if config_value.config_id in test_values:
            assert config_value.value == test_values[config_value.config_id]


def test_configuration_settings():
    prepare_clean_basedir()
    prepare_new_env_master_key()
    config = create_configuration()

    for key, value in new_values.items():
        config.save_new_value(key, value)
        assert config_items_new.get(key).value == value

    config = create_configuration()     # read in a second time with new values

    for key, value in new_values.items():
        assert config_items.get(key).value == value

    for key, value in new_values_immediate.items():
        config.save_new_value(key, value, apply_immediately=True)
        assert config_items_new.get(key) == None
        assert config_items.get(key).value == value
        assert config._values[key] == value

    config = create_configuration()      # read in the saved configuration
    for key, value in new_values_immediate.items():
        assert config.get_value(key) == value