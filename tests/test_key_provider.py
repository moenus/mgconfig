from mgconfig.key_provider import KeyProvider
from mgconfig.secure_store import generate_key_str
from pathlib import Path
import json
from mgconfig.helpers import lazy_build_config_id, section_SEC
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
keyring.set_password(SERVICE_NAME, 'salt', SALT_KEY)


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
    set_config('salt', 'keyring', 'salt')

    prepare_keyfile()

    provider = KeyProvider(config)

    master_key = provider.get('master_key')
    try:
        salt = provider.get('salt')
    except:
        provider.set(
            'salt', 'ZwJrh5riYXfdOj+c9PGQpZjMwbmTnV7G+sopW/qjTyw=')
        salt = provider.get('salt')

    print(master_key)
    print(salt)


if __name__ == '__main__':
    test_key_provider_module()
    print('Finished.')
