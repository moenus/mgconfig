# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

# -----------------------------------------------------------------------------
# Project Name: mgconfig
# File: __init__.py
# Author: Moenus
# License: MIT License (https://opensource.org/licenses/MIT)
#
# Copyright (c) 2025 Moenus@
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

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
