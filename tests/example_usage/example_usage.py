from mgconfig import Configuration, DefaultValues, PostProcessing, DefaultFunctions, ConfigTypes, configuration_logger
from ext_default_functions import default_hostname, default_timezone
from ext_postprocessing import extend_timezone_configuration, LOCAL_TZ_ID
from ext_config_types import parse_filename
import logging
from ext_app_header import AppHeader

CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__test.yml"
]


# ---------------------------------------------------------------------
# configuration types extensions - example
# ---------------------------------------------------------------------
ConfigTypes.add_type('minutes', int,
                     ConfigTypes._parse_int_positive, str, None)
ConfigTypes.add_type('seconds', int,
                     ConfigTypes._parse_int_positive, str, None)
ConfigTypes.add_type('filename', str, parse_filename, None, None)


# ---------------------------------------------------------------------
# application logger example
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
app_logger = logging.getLogger("example_usage")
configuration_logger.replace_logger(app_logger)

# ---------------------------------------------------------------------
# default values - example
# ---------------------------------------------------------------------
DefaultValues().clear()

# ---------------------------------------------------------------------
# default functions - example
# ---------------------------------------------------------------------
DefaultFunctions().add('hostname', default_hostname)
DefaultFunctions().add('timezone', default_timezone)

# ---------------------------------------------------------------------
# post-processing - example
# ---------------------------------------------------------------------
PostProcessing().add(extend_timezone_configuration)

# ---------------------------------------------------------------------
# application header values - example
# ---------------------------------------------------------------------
AppHeader.name = 'testapp'
AppHeader.title = 'Application Title'
AppHeader.prefix = 'app'
AppHeader.version = 'V1.0'

# ---------------------------------------------------------------------
# configuration item value creation
# ---------------------------------------------------------------------
config = Configuration(CONFIG_DEFINITIONS_YAML)

# ---------------------------------------------------------------------
# checking specific post-processing results
# ---------------------------------------------------------------------
if config.extended_item_exists(LOCAL_TZ_ID):
    app_logger.info(
        f'Local timezone: {config.get_extended_item(LOCAL_TZ_ID).zone}')
    # value of 'local_tz' can be directly accessed as property using config.extended.local_tz
else:
    app_logger.info(
        f'Configuration value for "{LOCAL_TZ_ID}" was not found.')
