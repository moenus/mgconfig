# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.key_provider import KeyProvider
from pathlib import Path
import json
from mgconfig.secure_store_helpers import generate_key_str
from tests.quicktests.t_helpers import get_test_filepath, prepare_clean_basedir
import keyring
import os


from mgconfig.config_values import config_values, ConfigValue


config_values.set( "sec_master_key_keystore", ConfigValue(None,'env','source'))
config_values.set( "sec_master_key_item_name", ConfigValue(None,'APP_KEY','source'))


KEYFILE = get_test_filepath("secure_keyfile.json")
SERVICE_NAME = 'mgconfig_test'


prepare_clean_basedir()
MASTER_KEY = generate_key_str()
os.environ["APP_KEY"] = MASTER_KEY
keyring.set_password(SERVICE_NAME, 'master_key', MASTER_KEY)





def prepare_keyfile():
    keydata = {'salt': 'abc', 'APP_KEY': 'xyz'}
    path = Path(KEYFILE).parent
    path.mkdir(parents=True, exist_ok=True)
    with open(KEYFILE, "w") as f:
        json.dump(keydata, f)


def test_key_provider_module():

    prepare_keyfile()

    provider = KeyProvider()

    master_key = provider.get('master_key')

    print(master_key)


if __name__ == '__main__':
    test_key_provider_module()
    print('Finished.')
