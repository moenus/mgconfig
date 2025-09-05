# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.config_defs import ConfigDefs
from tests.quicktests.t_helpers import CONFIG_DEFINITIONS_YAML, DefaultValues

default_function_values = {}

def test_create_config_defs():
    DefaultValues().clear()
    DefaultValues().add('app_name', 'testapp')

    default_values = DefaultValues().dict

    cfg_defs = ConfigDefs(CONFIG_DEFINITIONS_YAML).items

    counter_default_values = 0
    counter_default_function_values = 0

    for config_data in cfg_defs.values():

        if config_data.config_id in default_values:
            assert default_values.get(
                config_data.config_id) == config_data.config_default
            counter_default_values += 1
            source = "dv"  # default function

        elif config_data.config_id in default_function_values:
            assert default_function_values.get(
                config_data.config_id) == config_data.config_default
            counter_default_function_values += 1
            source = "df"  # default function
        else:
            source = "cd"  # configuration definition file
        print(f'{(config_data.config_id).ljust(25)} {(config_data.config_type).ljust(15)} {source}: {config_data.config_default}')

    assert counter_default_values == len(default_values)
    assert counter_default_function_values == len(default_function_values)


if __name__ == '__main__':
    test_create_config_defs()
