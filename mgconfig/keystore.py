import keyring
import os
import json
from pathlib import Path
from .helpers import ConstConfigs


class KeyStore:
    keystore_name = 'unknown'
    
    def __init__(self):
        self.params = None
        self.mandatory_conf_names = []

    def get(self, name):
        pass

    def set(self, name, value):
        raise ValueError(
            f'Cannot update keys in keystore {self.keystore_type}.')

    def get_param(self, name):
        if name not in self.params:
            raise ValueError(
                f'Configuration item {name} for keystore {self.keystore_type} is missing.')
        return self.params[name]

    def configure(self, config_params=None):
        self.params = {}
        for conf_name in self.mandatory_conf_names:
            self.params[conf_name] = config_params.get(ConstConfigs.get_config_id(conf_name))
            if self.params[conf_name] is None:
                raise ValueError(
                    f'Mandatory parameter {conf_name} for keystore {self.keystore_name} not found.')

    def check_configuration(self):
        if self.params is None:
            raise ValueError(
                f'Keystore {self.keystore_type} is not configured properly.')


config_keyfile = ConstConfigs('keyfile_filepath')
config_service_name = ConstConfigs('keyring_service_name')

class KeyStoreFile(KeyStore):
    keystore_name = 'file'
    
    def __init__(self):
        self.filedata = None
        self.mandatory_conf_names = [config_keyfile.name]

    @property
    def filepath(self):
        return self.get_param(config_keyfile.name)

    def check_configuration(self):
        super().check_configuration()
        if not self.filedata:
            self.filedata = {}
            if os.path.exists(self.filepath):
                with open(self.filepath, "r") as f:
                    self.filedata = json.load(f)
            if self.filedata is None or self.filedata == {}:
                raise ValueError(
                    f'Could not read keystore data from file {self.filepath}.')

    def get(self, item_name):
        self.check_configuration()
        if self.filedata:
            return self.filedata.get(item_name)

    def set(self, item_name, value: str):
        self.check_configuration()
        self.filedata[item_name] = value
        self._save()

    def _save(self):
        if not os.path.exists(self.filepath):
            path = Path(self.filepath).parent
            path.mkdir(parents=True, exist_ok=True)
        else:
            if not os.access(self.filepath, os.W_OK):
                return False
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.filedata, f)
            return True
        except:
            return False


class KeyStoreKeyring(KeyStore):
    keystore_name = 'keyring'

    def __init__(self):
        self.mandatory_conf_names = [config_service_name.name]

    @property
    def service_name(self):
        return self.get_param(config_service_name.name)

    def get(self, item_name):
        self.check_configuration()
        return keyring.get_password(
            self.service_name, item_name)

    def set(self, item_name, value: str):
        self.check_configuration()
        keyring.set_password(self.service_name,
                             item_name, value)


class KeyStoreEnv(KeyStore):
    keystore_name = 'env'

    def get(self, item_name):
        return os.getenv(item_name)


class KeyStores:
    _ks_dict = {}

    @classmethod
    def add(cls, ks: KeyStore):
        cls._ks_dict[ks.keystore_name] = ks

    @classmethod
    def get(cls, name):
        return cls._ks_dict.get(name)

    @classmethod
    def contains(cls, name):
        return name in cls._ks_dict


KeyStores.add(KeyStoreEnv())
KeyStores.add(KeyStoreFile())
KeyStores.add(KeyStoreKeyring())
