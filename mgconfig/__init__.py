from .helpers import logger, ConstSection, ConstConfig, Section
from .extension_system import DefaultValues, DefaultFunctions, PostProcessing
from .configuration import Configuration
from .config_types import ConfigTypes

__version__ = "0.5"

configuration_logger = logger 

# TODO: Can configuration values be None?

# the predefined classes for section handles and predefined objects for resolving an config id at runtime
# are used in mgconfig code to find the configuration for configuration value stores. They will be resolved
# to the actual values at runtime.
# Below they are initialized to some start values but they can be overwritten in your application code
# before the configuration object is initialized.


# Predefined section handles (Sections.APP and Sections.SEC) are initialized with a prefix value
# ConstSection(Section.APP).section_prefix = 'app'

# Predefined configuration id handles (Objects of type LazyConfigId) are initialized with a config id value 
# Example: ConstConfig('configfile').config_id = 'app_configfile'
