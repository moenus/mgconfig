# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

from mgconfig.keystore import KeyStores
from mgconfig.helpers import lazy_build_config_id, section_SEC

class Key:
    def __init__(self, keystore_name, item_name: str):
        self.keystore_name = keystore_name
        self.item_name = item_name
        self.item_value = None

    @property
    def value(self):
        if self.item_value is None:
            self._retrieve_key()
        return self.item_value

    @value.setter
    def value(self, item_value):
        KeyStores.get(self.keystore_name).set(self.item_name, item_value)
        self.item_value = item_value

    def __str__(self):
        return str(self.item_value)

    def _retrieve_key(self):
        self.item_value = KeyStores.get(self.keystore_name).get(self.item_name)
        if self.item_value is None:
            raise ValueError(
                f'Keystore {self.keystore_name} cannot provide a value for {self.item_name}.')


SALTNAME = 'salt'
MASTERKEYNAME = 'master_key'

ITEM_NAME_TAG = 'item_name'
KEYSTORE_NAME_TAG = 'keystore'


def get_from_conf(conf, key_name, value_name):
    config_id = lazy_build_config_id(section_SEC, key_name + "_" + value_name)
    value = conf.get(config_id)
    if value is None:
        raise ValueError(f'Cannot find {config_id} for {key_name}')
    return value


class KeyProvider:
    def __init__(self, config):
        self._keys = {}
        self.valid_keys = [SALTNAME, MASTERKEYNAME]
        for key_name in self.valid_keys:
            if not key_name in self.valid_keys:
                raise ValueError(f'Invalid key name {key_name}')
            keystore_name = get_from_conf(config, key_name, KEYSTORE_NAME_TAG)
            if not KeyStores.contains(keystore_name):
                raise ValueError(f'Invalid keystore name {keystore_name}')
            KeyStores.get(keystore_name).configure(config)
            item_name = get_from_conf(config, key_name, ITEM_NAME_TAG)
            self._keys[key_name] = Key(keystore_name, item_name)


    def get(self, name):
        if name in self._keys:
            return self._keys.get(name).value

    def set(self, name, value):   
        if name in self._keys:  
            self._keys.get(name).value = value

