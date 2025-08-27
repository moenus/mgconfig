# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig import Configuration, ConfigTypes, configuration_logger, DefaultValues
import logging


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__example.yml"
]


# ---------------------------------------------------------------------
# application logger example
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
app_logger = logging.getLogger("example_usage")
configuration_logger.replace_logger(app_logger)

# # ---------------------------------------------------------------------
# # default values - example
# # ---------------------------------------------------------------------
DefaultValues().clear()
DefaultValues().add('app_name', 'appname')

# ---------------------------------------------------------------------
# configuration item value creation
# ---------------------------------------------------------------------
config = Configuration(CONFIG_DEFINITIONS_YAML)


print(ConfigTypes.list_all())
print(config.data_rows)