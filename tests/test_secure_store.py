from mgconfig import secure_store
from t_helpers import remove_file, get_test_filepath
import os

TEST_ITEM_TEXT = 'this is a password test'
TEST_ITEM_NAME = 'test_password'

KEYSTORE_FILE = get_test_filepath("keystore_test.json")

os.environ["APP_KEY"] = secure_store.generate_key_str()


class DummyProvider(dict):
    def __init__(self):
        self.dummyprovider = {
            'master_key': 'ZwJrh5riYXfdOj+c9PGQpZjMwbmTnV7G+sopW/qjTyw=',
            'salt_key': 'XBGG61LZC+o48Rsqmod2nnZZxTkROW2JuJoopOb/QFg='
        }

    def get(self, name):
        return self.dummyprovider.get(name)

    def set(self, name, value):
        self.dummyprovider[name] = value



def run_cycle(provider1, provider2):
    print(f'\n------------------------------- start cycle with empty file store')
    remove_file(KEYSTORE_FILE)
    store(provider1, TEST_ITEM_TEXT)
    return TEST_ITEM_TEXT == retrieve(provider2)


def store(provider, text):
    secure_keystore = secure_store.SecureStore(
        KEYSTORE_FILE, provider)
    secure_keystore.store_secret(TEST_ITEM_NAME, text)
    secure_keystore.save_securestore()


def retrieve(provider):
    secure_keystore = secure_store.SecureStore(
        KEYSTORE_FILE, provider)
    test_item_str_decoded = secure_keystore.retrieve_secret(TEST_ITEM_NAME)
    return test_item_str_decoded


def validate_master_key(provider):
    secure_keystore = secure_store.SecureStore(
        KEYSTORE_FILE, provider)
    return secure_keystore.validate_master_key()


def prepare_auto_key_exchange(provider):
    secure_keystore = secure_store.SecureStore(
        KEYSTORE_FILE, provider)
    return secure_keystore.prepare_auto_key_exchange()


def test_secure_store_module_basic():

    provider = DummyProvider()
    assert run_cycle(provider, provider) == True
    assert validate_master_key(provider) == True

def test_secure_store_module_wrong_salt():

    provider = DummyProvider()
    provider2 = DummyProvider()
    # assign wrong salt key
    provider2.set('salt_key', secure_store.generate_key_str())
    assert run_cycle(provider, provider2) == False
    assert validate_master_key(provider2) == False

def test_secure_store_module_wrong_master():

    provider = DummyProvider()
    provider2 = DummyProvider()
    # assign wrong master key
    provider2.set('master_key', secure_store.generate_key_str())
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
    print(secure_store.generate_key_str())
    test_secure_store_key_exchange()
    print('Finished.')
