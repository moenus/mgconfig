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

from .config_key_map import ConfigKeyMap
from .extension_system import DefaultValues, DefaultFunctions, PostProcessing
from .configuration import Configuration
from .config_types import ConfigTypes
from .config_defs import ConfigDefs
from ._test_support import prepare_temp_data_directory, internal_reset
from .sec_store_crypt import generate_master_key_str
import logging


__version__ = "0.2.1-alpha"

# ---------------------------------------------------------------------
# basic logging preparation
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)

"""Initialize the logger with a default console handler."""
logger.setLevel(logging.INFO)
if not logger.handlers:  # avoid duplicate handlers
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

