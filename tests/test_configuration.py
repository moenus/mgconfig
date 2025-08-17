# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from datetime import time
from pathlib import Path
from t_helpers import prepare_clean_basedir, create_configuration, set_app_header, prepare_new_env_master_key


BASE_DIRECTORY_PATH = prepare_clean_basedir()

set_app_header()

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
    'tst_secret': 'newpw'
}

new_values_immediate = {
    'tst_string': 'newstring_immediate',
    'tst_integer': 600,
    'tst_bool': True,
    'tst_time': time(13, 11, 25),
    'tst_path': Path(r'\dir\c.txt'),
    'tst_secret': 'geheim'
}

new_values_immediate_ext = {
    'tst_path': Path(r'\dir\c.txt'),
}


def test_configuration_reading():
    prepare_new_env_master_key()
    config = create_configuration()

    assert config.app_name == test_values['app_name']

    for key, value in test_values.items():
        assert config.get(key) == value

    for config_value in config._config_values.values():
        assert config_value.value_src == config_value.output_current()


def test_configuration_settings():
    prepare_new_env_master_key()
    config = create_configuration()

    for key, value in new_values.items():
        config.save_new_value(key, value)
        assert config._config_values[key].value_new == value

    config = create_configuration()     # read in a second time with new values

    for key, value in new_values.items():
        assert config._config_values[key].value == value

    for key, value in new_values_immediate.items():
        config.save_new_value(key, value, apply_immediately=True)
        assert config._config_values[key].value_new == None
        assert config._config_values[key].value == value
        assert config.__dict__[key] == value

    config = create_configuration()      # read in the saved configuration
    for key, value in new_values_immediate.items():
        assert config.get(key) == value


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
    for config_def in config._cfg_def_dict.values():
        id = config_def.config_id
        val_main = prep(config.__dict__.get(id))
        val_obj = config._config_values.get(id)
        val_type = config_def.config_type
        if val_obj:
            val_src = prep(val_obj.value_src)
            val_out = prep(val_obj.output_current())
            val_str = prep(val_obj.display_current())
        else:
            val_src = val_out = val_str = ''
        print(f'{(f'{id}: {val_type}').ljust(25)} {
              val_main} {val_src} {val_out} {val_str}')


if __name__ == '__main__':
    # test_configuration_reading()

    configuration_values_print()
    print('finished successfully')
