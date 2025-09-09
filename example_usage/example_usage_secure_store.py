# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.secure_store import SecureStore
from mgconfig.sec_store_crypt import generate_master_key_str
from pathlib import Path

import os

root_dir = os.path.dirname(os.path.abspath(__file__))
test_basedir = Path(root_dir) / 'temp_basedir'


def get_test_filepath(filename):
    return Path(test_basedir) / filename


def remove_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)


DEMO_ITEM_TEXT = 'this is a password test'
DEMO_ITEM_NAME = 'test_password'

KEYSTORE_FILE = get_test_filepath("keystore_demo.json")

os.environ["APP_KEY"] = generate_master_key_str()


class DummyProvider(dict):
    def __init__(self):
        self.dummyprovider = {
            'master_key': 'ZwJrh5riYXfdOj+c9PGQpZjMwbmTnV7G+sopW/qjTyw=',
        }

    def get(self, name):
        return self.dummyprovider.get(name)

    def set(self, name, value):
        self.dummyprovider[name] = value



def run_cycle(provider1, provider2):
    print(f'\n------------------------------- start cycle with empty file store')
    remove_file(KEYSTORE_FILE)
    store(provider1, DEMO_ITEM_TEXT)
    return DEMO_ITEM_TEXT == retrieve(provider2)


def store(provider, text):
    with SecureStore(
        KEYSTORE_FILE, 
        provider
        ) as ss:
        ss.store_secret(DEMO_ITEM_NAME, text)


def retrieve(provider):
    with SecureStore(
        KEYSTORE_FILE, 
        provider
        ) as ss:
        test_item_str_decoded =ss.retrieve_secret(DEMO_ITEM_NAME)
        return test_item_str_decoded


def validate_master_key(provider):
    with SecureStore(
        KEYSTORE_FILE, 
        provider
        ) as ss:
        return ss.validate_master_key()


def prepare_auto_key_exchange(provider):
    with SecureStore(
        KEYSTORE_FILE, 
        provider
        ) as ss:
        return ss.prepare_auto_key_exchange()


def test_secure_store_module_basic():

    provider = DummyProvider()
    assert run_cycle(provider, provider) == True
    assert validate_master_key(provider) == True


def test_secure_store_module_wrong_master():

    provider = DummyProvider()
    provider2 = DummyProvider()
    # assign wrong master key
    provider2.set('master_key', generate_master_key_str())
    assert run_cycle(provider, provider2) == False
    assert validate_master_key(provider2) == False


def test_secure_store_key_exchange():

    provider = DummyProvider()
    assert run_cycle(provider, provider) == True
    provider2 = DummyProvider()
    provider2.set('master_key', prepare_auto_key_exchange(provider))

    # will run the auto key exchange
    assert validate_master_key(provider2) == True
    assert validate_master_key(provider) == False  # old key not valid any more

    assert run_cycle(provider2, provider2) == True
    assert run_cycle(provider2, provider) == False


if __name__ == '__main__':
    print(generate_master_key_str())
    # test_secure_store_key_exchange()
    print('Finished.')
