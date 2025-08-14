import os
import yaml
from .helpers import logger,  config_securestorefile, config_configfile
from .secure_store import SecureStore
from .key_provider import KeyProvider
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from enum import Enum


# config_configfile = ConstConfigs('configfile')
# config_securestorefile = ConstConfigs('securestore_file')


class ConfigValueSource(str, Enum):
    """Enumerates the possible configuration value sources."""
    CFGFILE = 'cfgfile'
    ENV_VAR = 'env_var'
    DEFAULT = 'default'
    SECRET = 'secret'


class ValueStore:
    def __init__(self, init_config, source: ConfigValueSource):
        self.config = init_config
        self.source = source

    def save_value(self, item_id: str, value: Any) -> bool:
        pass

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        pass


class ValueStoreSecure(ValueStore):
    def __init__(self, init_config):
        """Initialize a file-based secure value store for storing secret strings like passwords.

        Args:
            init_config: The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.SECRET)
        self.securestore_file = init_config.get(config_securestorefile.config_id)
        # initialize key provider with the configuration values from Configuration object
        self.key_provider = KeyProvider(init_config)
        try:
            secure_store = self._get_new_secure_store()
            if not secure_store.validate_master_key():
                logger.info(
                    'Master key invalid or secure store corrupted.')
            else:
                logger.info('Secure store was successfully initialized.')
        except Exception as e:
            logger.error(f'Cannot initialize secure store: {e}')

    def _get_new_secure_store(self):
        return SecureStore(
            self.securestore_file,
            self.key_provider
        )

    def save_value(self, item_id, value) -> bool:
        try:
            secure_store = self._get_new_secure_store()
            secure_store.store_secret(item_id, value)
            secure_store.save_securestore()
            logger.info(f'Secret {item_id} saved to keystore.')
            return True
        except Exception as e:
            logger.error(f'Cannot store secret value for id {item_id}: {e}')
        return False

    def retrieve_value(self, item_id) -> tuple[Any, str]:
        try:
            secure_store = self._get_new_secure_store()
            return secure_store.retrieve_secret(item_id), self.source
        except Exception as e:
            logger.error(f'Cannot retrieve secret value for id {item_id}: {e}')
            return None, self.source

    def prepare_new_masterkey(self) ->str:
        try:
            secure_store = self._get_new_secure_store()
            new_masterkey_str = secure_store.prepare_auto_key_exchange()
        except Exception as e:
            logger.error(f'Cannot prepare new master key: {e}')
            return None
        logger.info('New master key generated. Auto-key-exchange prepared.')
        return new_masterkey_str


class ValueStoreFile(ValueStore):
    """Value store that retrieves and stores configuration in a YAML file."""

    def __init__(self, init_config):
        """Initialize a file-based value store.

        Args:
            init_config: The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.CFGFILE)
        self.config_file = self.config._config_values.get(config_configfile.config_id).value
        self.configfile_content = self._read_configfile()

    def _read_configfile(self) -> dict:
        """Read configuration data from the YAML config file.

        Returns:
            dict: The contents of the configuration file, or an empty dict if not found.
        """
        if os.path.exists(self.config_file):
            logger.info(f'Reading config from file "{self.config_file}"')
            with open(self.config_file, "r") as file:
                # Use safe_load to prevent code execution
                return yaml.safe_load(file)
        else:
            logger.info(f'No config file "{self.config_file}" found.')
            return {}

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieve a value from the YAML configuration file.

        Args:
            item_id (str): The configuration item identifier.

        Returns:
            tuple[Any, str]: The retrieved value and the source type.
        """
        config_section, config_name = self._get_section_and_name(item_id)
        if config_section in self.configfile_content and config_name in self.configfile_content[config_section]:
            return self.configfile_content[config_section][config_name], self.source
        return None, self.source

    def save_value(self, item_id, value) -> bool:
        config_section, config_name = self._get_section_and_name(item_id)
        if config_section not in self.configfile_content:
            self.configfile_content[config_section] = {}
        self.configfile_content[config_section][config_name] = value
        return self._write_configfile()

    def _write_configfile(self) -> bool:
        config_path = os.path.dirname(self.config_file)
        try:
            os.makedirs(config_path, exist_ok=True)
        except Exception as e:
            logger.error(
                f"Directory '{config_path}' could not be prepared: {e}.")
            return False
        try:
            with open(self.config_file, "w") as file:
                yaml.dump(self.configfile_content, file,
                          default_flow_style=False)
            return True
        except Exception as e:
            logger.error(
                f"File '{self.config_file}' could not be written: {e}.")
            return False

    def _get_section_and_name(self, item_id):
        cfg_def = self.config._cfg_def_dict[item_id]
        return cfg_def.config_section, cfg_def.config_name


class ValueStoreEnv(ValueStore):

    def __init__(self, init_config):
        """Initialize an environment-variable-based value store.

        Args:
            init_config: The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.ENV_VAR)

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        config_env = self._get_config_env(item_id)
        if config_env is not None:
            return os.getenv(config_env), self.source
        return None, self.source

    def _get_config_env(self, item_id):
        cfg_def = self.config._cfg_def_dict[item_id]
        return cfg_def.config_env


class ValueStoreDefault(ValueStore):
    def __init__(self, init_config):
        """Initialize a value store that contains default values.

        Args:
            init_config: The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.DEFAULT)

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        config_default = self._get_config_default(item_id)
        if config_default:
            return config_default, self.source
        return None, self.source

    def _get_config_default(self, item_id):
        cfg_def = self.config._cfg_def_dict[item_id]
        return cfg_def.config_default


class ValueStores:
    value_stores = {}

    @classmethod
    def get(cls, value_store_class: Type[ValueStore], init_config=None):
        if value_store_class in cls.value_stores:
            # this value store was already initialized
            return cls.value_stores.get(value_store_class)
        if not issubclass(value_store_class, ValueStore):
            raise ValueError(f'Value store class {value_store_class} invalid.')
        if init_config is None:
            raise ValueError(
                f'Value store class {value_store_class} is not initialized.')
        try:
            new_value_store = value_store_class(init_config)
            cls.value_stores[value_store_class] = new_value_store
            return new_value_store
        except Exception as e:
            raise ValueError(
                f'Cannot initialize value store {value_store_class}! {e}')
