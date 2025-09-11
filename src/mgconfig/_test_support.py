# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import shutil
import os
from pathlib import Path
from .extension_system import DefaultValues, DefaultFunctions, PostProcessing
from .configuration import Configuration
from .config_types import ConfigTypes
from .config_defs import ConfigDefs

import logging
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# test environment preparation
# ---------------------------------------------------------------------

# Creates a new empty data directory and sets the corresponding environment variable
# so examples and tests can run against it. The directory is created in the parent
# directory of this file and is not automatically removed after the test, allowing
# manual inspection afterwards.
def prepare_temp_data_directory(file: str) -> Path:
    # prepare a new, empty data directory for this example  
    test_basedir = Path(file).resolve().parent / 'temp_basedir'
    shutil.rmtree(test_basedir, ignore_errors=True)
    test_basedir.mkdir(exist_ok=True)

    # provide basic values for app_basedir in environment variable
    os.environ["DATA_DIRECTORY"] = test_basedir.as_posix()
    logger.info(f'New and empty data directory {test_basedir} provided.')
    return test_basedir


def internal_reset():
    DefaultValues().clear()
    DefaultFunctions().clear()
    PostProcessing().clear()
    ConfigDefs.reset_instance()
    Configuration.reset_instance()
    
    