# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from datetime import time
from pathlib import Path

import os
import shutil
from mgconfig import Configuration, DefaultValues
from mgconfig.config_defs import ConfigDefs
from mgconfig.config_types import ConfigTypes
from mgconfig.secure_store_helpers import generate_key_str
from mgconfig.config_values import config_values, config_values_new


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__test.yml"
]

root_dir = os.path.dirname(os.path.abspath(__file__))
test_basedir = Path(root_dir) / 'temp_basedir'


def prepare_clean_basedir():
    os.environ["DATA_DIRECTORY"] = test_basedir.as_posix()
    shutil.rmtree(test_basedir, ignore_errors=True)
    test_basedir.mkdir(exist_ok=True)
    return test_basedir


def create_configuration():
    DefaultValues().clear()
    DefaultValues().add('app_name', 'testapp')
    Configuration.reset_instance()
    return Configuration(CONFIG_DEFINITIONS_YAML)


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
}

new_values_immediate = {
    'tst_string': 'newstring_immediate',
    'tst_integer': 600,
    'tst_bool': True,
    'tst_time': time(13, 11, 25),
    'tst_path': Path(r'\dir\c.txt'),
}

new_values_immediate_ext = {
    'tst_path': Path(r'\dir\c.txt'),
}


def configuration_reading():
    config = create_configuration()

    assert config.app_name == test_values['app_name']

    for key, value in test_values.items():
        assert config.get_value(key) == value

    for config_value in config_values.values():
        if config_value.config_id in test_values:
            assert config_value.value == test_values[config_value.config_id]


def configuration_changes():
    config = create_configuration()

    for key, value in new_values.items():
        config.save_new_value(key, value)
        assert config_values_new.get(key).value == value

    config = create_configuration()     # read in a second time with new values

    for key, value in new_values.items():
        assert config_values.get(key).value == value

    for key, value in new_values_immediate.items():
        config.save_new_value(key, value, apply_immediately=True)
        assert config_values_new.get(key) == None
        assert config_values.get(key).value == value
        assert config.__dict__[key] == value

    config = create_configuration()      # read in the saved configuration
    for key, value in new_values_immediate.items():
        assert config.get_value(key) == value


def configuration_values_print():
    def prep(value):
        return (f'{value}: {type(value).__name__}').ljust(25)

    config = create_configuration()
    for key, value in new_values.items():
        config.save_new_value(key, value)
    print('------------------------------------')
    for row in config.data_rows:
        print(str(row))

    print('------------------------------------')
    for config_def in ConfigDefs().values():
        id = config_def.config_id
        val_main = prep(config.__dict__.get(id))
        val_obj = config_values.get(id)
        val_type = config_def.config_type
        if val_obj:
            # val_src = prep(val_obj.value_src)
            val_out = prep(ConfigTypes.output_value(val_obj.value, config_def.config_type))
            # val_out = prep(val_obj.output_current())
            val_str = prep(str(val_obj))
        else:
            val_src = val_out = val_str = ''
        print(f'{(f'{id}: {val_type}').ljust(30)} {
              val_main} {val_out} {val_str}')


if __name__ == '__main__':
    os.environ["APP_KEY"] = generate_key_str()
    configuration_reading()
    configuration_changes()
    configuration_values_print()
    print('finished successfully')
