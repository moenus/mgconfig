# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.secure_store import SecureStore
from mgconfig.secure_store_helpers import generate_key_str
import os
from pathlib import Path 

TEST_ITEM_TEXT = 'this is a password test'
TEST_ITEM_NAME = 'test_password'


KEYSTORE_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / 'temp_basedir' / "keystore_test.json"

os.environ["APP_KEY"] = generate_key_str()

def remove_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        
class DummyProvider(dict):
    def __init__(self):
        self.dummyprovider = {
            'master_key': generate_key_str(),
        }

    def get(self, name):
        return self.dummyprovider.get(name)

    def set(self, name, value):
        self.dummyprovider[name] = value



def run_cycle(provider1, provider2):
    print(f'\n------------------------------- start cycle with empty file store')
    store(provider1, TEST_ITEM_TEXT)
    return TEST_ITEM_TEXT == retrieve(provider2)


def store(provider, text):
    with SecureStore(
        KEYSTORE_FILE, 
        provider
        ) as ss:
        ss.store_secret(TEST_ITEM_NAME, text)


def retrieve(provider):
    with SecureStore(
        KEYSTORE_FILE, 
        provider
        ) as ss:
        test_item_str_decoded =ss.retrieve_secret(TEST_ITEM_NAME)
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

    remove_file(KEYSTORE_FILE)
    provider = DummyProvider()
    assert run_cycle(provider, provider) == True
    assert validate_master_key(provider) == True


def test_secure_store_module_wrong_master():
    
    remove_file(KEYSTORE_FILE)
    provider = DummyProvider()
    provider2 = DummyProvider()
    # assign wrong master key
    provider2.set('master_key', generate_key_str())
    assert run_cycle(provider, provider2) == False
    assert validate_master_key(provider2) == False


def test_secure_store_key_exchange():

    remove_file(KEYSTORE_FILE)
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
    print(generate_key_str())
    # test_secure_store_key_exchange()
    print('Finished.')
