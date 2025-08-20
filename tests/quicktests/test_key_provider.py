# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.key_provider import KeyProvider
from mgconfig.secure_store import SecureStore
from pathlib import Path
import json
from mgconfig.helpers import lazy_build_config_id, section_SEC
from mgconfig.secure_store_helpers import generate_key_str
from tests.quicktests.t_helpers import get_test_filepath, prepare_clean_basedir
import keyring
import os

KEYFILE = get_test_filepath("secure_keyfile.json")
SERVICE_NAME = 'mgconfig_test'
config = {}

prepare_clean_basedir()
MASTER_KEY = generate_key_str()
os.environ["APP_KEY"] = MASTER_KEY
keyring.set_password(SERVICE_NAME, 'master_key', MASTER_KEY)


def set_config(key_name, keystore_name, item_name):
    config[
        lazy_build_config_id(section_SEC, key_name + '_keystore')
    ] = keystore_name
    config[
        lazy_build_config_id(section_SEC, key_name + '_item_name')
    ] = item_name
    config[
        lazy_build_config_id(section_SEC, 'keyfile_filepath')
    ] = KEYFILE
    config[
        lazy_build_config_id(section_SEC, 'keyring_service_name')
    ] = SERVICE_NAME


def prepare_keyfile():
    keydata = {'salt': 'abc', 'APP_KEY': 'xyz'}
    path = Path(KEYFILE).parent
    path.mkdir(parents=True, exist_ok=True)
    with open(KEYFILE, "w") as f:
        json.dump(keydata, f)


def test_key_provider_module():
    set_config('master_key', 'env', 'APP_KEY')

    prepare_keyfile()

    provider = KeyProvider(config)

    master_key = provider.get('master_key')

    print(master_key)


if __name__ == '__main__':
    test_key_provider_module()
    print('Finished.')
