# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
from tests.quicktests.t_helpers import prepare_clean_basedir, create_configuration, prepare_new_env_master_key
from mgconfig import get_new_masterkey

CONFIG_ID = 'tst_secret'

BASE_DIRECTORY_PATH = prepare_clean_basedir()


def test_configuration_secrets():
    prepare_new_env_master_key()
    prepare_clean_basedir()
    
    config = create_configuration()

    assert config.save_new_value(CONFIG_ID,'passwort_1')
    assert config.get_config_object(CONFIG_ID).value == 'passwort_1' 

  
    new_masterkey = get_new_masterkey()
    assert isinstance(new_masterkey, str)
    os.environ["APP_KEY"] = new_masterkey

    config = create_configuration()     # read in a second time after changing masterkey

    assert config.tst_secret == 'passwort_1'
     
    # config.save_new_value(CONFIG_ID,'passwort_2',apply_immediately=True)
    # assert config._config_values[CONFIG_ID].value == 'passwort_2' 

    # config = create_configuration()     # read in a second time after changing masterkey

    # assert config._config_values[CONFIG_ID].value == 'passwort_2'
    