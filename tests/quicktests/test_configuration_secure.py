# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import pytest
from tests.quicktests.t_helpers import prepare_clean_basedir, create_configuration, prepare_new_env_master_key
from mgconfig import generate_master_key_str

CONFIG_ID = 'tst_secret'


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and cleanup test environment."""
    # Store original env var if it exists
    original_key = os.environ.get("APP_KEY")
    
    # Setup clean environment
    test_dir = prepare_clean_basedir()
    prepare_new_env_master_key()
    
    yield test_dir
    
    # Cleanup
    try:
        if original_key:
            os.environ["APP_KEY"] = original_key
        else:
            del os.environ["APP_KEY"]
    except KeyError:
        pass

def test_configuration_secrets(setup_teardown):
    """Test secure configuration value handling with master key rotation."""
    # First configuration with initial master key
    config1 = create_configuration()
    assert config1.save_new_value(CONFIG_ID, 'passwort_1')
    assert config1.get_config_item(CONFIG_ID).value == 'passwort_1'
    
    # Get and set new master key
    new_masterkey = generate_master_key_str()
    assert isinstance(new_masterkey, str)
    os.environ["APP_KEY"] = new_masterkey
    
    # Force configuration reload with new key
    config2 = create_configuration()
    
    # Verify value can still be read with new key
    assert config2.tst_secret == 'passwort_1'
    
    # Verify both configurations work
    assert config1.tst_secret == 'passwort_1'
    assert config2.tst_secret == 'passwort_1'
     

    