# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig import Configuration, DefaultValues, PostProcessing, DefaultFunctions, ConfigTypes
from ext_default_functions import default_hostname, default_timezone
from ext_postprocessing import extend_timezone_configuration, LOCAL_TZ_ID
from ext_config_types import parse_filename
import logging

logger = logging.getLogger(__name__)

CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__example.yml"
]


# # ---------------------------------------------------------------------
# # configuration types extensions - example
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
# configuration item value creation
# ---------------------------------------------------------------------
config = Configuration(CONFIG_DEFINITIONS_YAML)

# ---------------------------------------------------------------------
# checking specific post-processing results
# ---------------------------------------------------------------------
if LOCAL_TZ_ID in config:
    logger.info(
        f'Local timezone: {config.get_value(LOCAL_TZ_ID).zone}')
    # value of 'local_tz' can be directly accessed as property using config.extended.local_tz
else:
    logger.info(
        f'Configuration value for "{LOCAL_TZ_ID}" was not found.')

print(ConfigTypes.list_all())