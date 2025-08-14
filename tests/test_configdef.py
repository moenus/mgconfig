from example_usage.ext_app_header import AppHeader
from mgconfig.helpers import lazy_build_config_id, section_APP
from mgconfig.configdef import ConfigDefs
from t_helpers import CONFIG_DEFINITIONS_YAML, set_app_header

default_function_values = {}

def test_create_config_defs():
    set_app_header()
    header_dict = AppHeader.get_header()
    header_values = {
        lazy_build_config_id(section_APP,key):
            value for key, value in header_dict.items()
    }

    cfg_defs = ConfigDefs(CONFIG_DEFINITIONS_YAML).config_defs

    counter_header_values = 0
    counter_default_function_values = 0

    for config_data in cfg_defs.values():

        if config_data.config_id in header_values:
            target_value = header_values.get(config_data.config_id)
            assert target_value == config_data.config_default
            counter_header_values += 1
            source = "hv"  # header value
        elif config_data.config_id in default_function_values:
            assert default_function_values.get(
                config_data.config_id) == config_data.config_default
            counter_default_function_values += 1
            source = "df"  # default function
        else:
            source = "cd"  # configuration definition file
        print(f'{(config_data.config_id).ljust(25)} {(config_data.config_type).ljust(15)} {source}: {config_data.config_default}')

    assert counter_header_values == len(header_values)
    assert counter_default_function_values == len(default_function_values)


if __name__ == '__main__':
    test_create_config_defs()
