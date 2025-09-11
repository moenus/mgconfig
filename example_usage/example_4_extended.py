# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig import Configuration, DefaultValues, PostProcessing, DefaultFunctions, ConfigTypes, prepare_temp_data_directory
from ext_default_functions import default_hostname, default_timezone
from ext_postprocessing import extend_timezone_configuration, LOCAL_TZ_ID
from ext_config_types import parse_filename

# this function create a new and empty data directory for testing purposes
prepare_temp_data_directory(__file__)


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def_2_intermediate.yaml",
    "config_defs/config_def_4_extended.yaml"
]


# # ---------------------------------------------------------------------
# # configuration types extension - examples
# # ---------------------------------------------------------------------
ConfigTypes.add_type('minutes', int,
                     ConfigTypes._parse_int_positive, str, None)
ConfigTypes.add_type('seconds', int,
                     ConfigTypes._parse_int_positive, str, None)
ConfigTypes.add_type('filename', str, parse_filename, None, None)


# # ---------------------------------------------------------------------
# # default values - example
# # ---------------------------------------------------------------------
DefaultValues().clear()
DefaultValues().add('app_name', 'Application_Name')

# # ---------------------------------------------------------------------
# # default functions - example
# # ---------------------------------------------------------------------
DefaultFunctions().add('hostname', default_hostname)
DefaultFunctions().add('timezone', default_timezone)

# # ---------------------------------------------------------------------
# # post-processing - example
# # ---------------------------------------------------------------------
PostProcessing().add(extend_timezone_configuration)

# ---------------------------------------------------------------------
# configuration instance creation
# ---------------------------------------------------------------------
config = Configuration(CONFIG_DEFINITIONS_YAML)

# ---------------------------------------------------------------------
# checking specific post-processing results
# ---------------------------------------------------------------------
if LOCAL_TZ_ID in config:
    print(
        f'Local timezone: {config.get_value(LOCAL_TZ_ID).zone}')
    # value of 'local_tz' can be directly accessed as property using config.extended.local_tz
else:
    print(
        f'Configuration value for "{LOCAL_TZ_ID}" was not found.')

print(ConfigTypes.list_all())
