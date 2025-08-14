from mgconfig.key_provider import KeyProvider
from mgconfig.secure_store import generate_key_str
from pathlib import Path
import json
from mgconfig.helpers import ConstSections
from t_helpers import get_test_filepath, prepare_clean_basedir
import keyring
import os

KEYFILE = get_test_filepath("secure_keyfile.json")
SERVICE_NAME = 'mgconfig_test'
config = {}

prepare_clean_basedir()
SALT_KEY = generate_key_str()
MASTER_KEY = generate_key_str()
os.environ["APP_KEY"] = MASTER_KEY
keyring.set_password(SERVICE_NAME, 'salt_key', SALT_KEY)


def set_config(key_name, keystore_name, item_name):
    config[ConstSections.SEC.build_id(
           key_name + '_keystore')] = keystore_name
    config[ConstSections.SEC.build_id(
           key_name + '_item_name')] = item_name
    config[ConstSections.SEC.build_id(
           'keyfile_filepath')] = KEYFILE
    config[ConstSections.SEC.build_id(
           'keyring_service_name')] = SERVICE_NAME


def prepare_keyfile():
    keydata = {'salt_key': 'abc', 'APP_KEY': 'xyz'}
    path = Path(KEYFILE).parent
    path.mkdir(parents=True, exist_ok=True)
    with open(KEYFILE, "w") as f:
        json.dump(keydata, f)


def test_key_provider_module():
    set_config('master_key', 'env', 'APP_KEY')
    set_config('salt_key', 'keyring', 'salt_key')

    prepare_keyfile()

    provider = KeyProvider(config)

    master_key = provider.get('master_key')
    try:
        salt_key = provider.get('salt_key')
    except:
        provider.set(
            'salt_key', 'ZwJrh5riYXfdOj+c9PGQpZjMwbmTnV7G+sopW/qjTyw=')
        salt_key = provider.get('salt_key')

    print(master_key)
    print(salt_key)


if __name__ == '__main__':
    test_key_provider_module()
    print('Finished.')
