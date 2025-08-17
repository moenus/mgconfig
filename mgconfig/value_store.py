# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import yaml
from .helpers import logger, config_securestorefile, config_configfile
from .secure_store import SecureStore
from .key_provider import KeyProvider
from .configdef import CDF
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from enum import Enum
from pathlib import Path


class ConfigValueSource(str, Enum):
    """Enumerates the possible configuration value sources."""
    
    CFGFILE = 'cfgfile'
    ENV_VAR = 'env_var'
    DEFAULT = 'default'
    ENCRYPT = 'encrypt'


class ValueStore:
    """Base class for configuration value storage backends.

    Attributes:
        config (Dict[str, str]): The configuration data used to initialize the store.
        source (ConfigValueSource): The source type of the configuration values.
    """    
    def __init__(self, init_config: Dict[str, str], source: ConfigValueSource):
        """Initialize a value store.

        Args:
            init_config (Dict[str, str]): The initial configuration data.
            source (ConfigValueSource): The source type for this store.
        """        
        self.config = init_config
        self.source = source

    def save_value(self, item_id: str, value: Any) -> bool:
        """Save a value in the store.

        Args:
            item_id (str): The configuration item identifier.
            value (Any): The value to store.

        Returns:
            bool: True if the value was saved successfully, False otherwise.
        """        
        pass

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieve a value from the store.

        Args:
            item_id (str): The configuration item identifier.

        Returns:
            tuple[Any, str]: The retrieved value and its source type.
        """        
        pass

    def _get_cfg_def_value(self, item_id: str, value_name: str) -> Optional[str]:
        """Retrieve a configuration definition attribute for an item.

        Args:
            item_id (str): The configuration item identifier.
            value_name (str): The attribute name in the configuration definition.

        Returns:
            Optional[str]: The configuration definition value, or None if not found.
        """        
        cfg_def = self.config._cfg_def_dict.get(item_id)
        if cfg_def is not None:
            return cfg_def.get(value_name)


class ValueStoreSecure(ValueStore):
    """Value store for securely storing sensitive data in a secure store file."""
        
    def __init__(self, init_config: Dict[str, str]):
        """Initialize a file-based secure value store for storing secret strings like passwords.

        Args:
            init_config (Dict[str, str]): The configuration object with initialization values.
        """
        super().__init__(init_config, ConfigValueSource.ENCRYPT)
        self.securestore_file = init_config.get(
            config_securestorefile.config_id)
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

    def _get_new_secure_store(self) -> SecureStore:
        """Create a new `SecureStore` instance.

        Returns:
            SecureStore: The initialized secure store.
        """        
        return SecureStore(
            self.securestore_file,
            self.key_provider
        )

    def save_value(self, item_id: str, value: str) -> bool:
        """Save a secret value securely.

        Args:
            item_id (str): The configuration item identifier.
            value (str): The secret value to store.

        Returns:
            bool: True if saved successfully, False otherwise.
        """        
        try:
            secure_store = self._get_new_secure_store()
            secure_store.store_secret(item_id, value)
            secure_store.save_securestore()
            logger.info(f'Secret {item_id} saved to keystore.')
            return True
        except Exception as e:
            logger.error(f'Cannot store secret value for id {item_id}: {e}')
        return False

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieve a secret value from the secure store.

        Args:
            item_id (str): The configuration item identifier.

        Returns:
            tuple[Any, str]: The retrieved secret and its source type.
        """        
        try:
            secure_store = self._get_new_secure_store()
            return secure_store.retrieve_secret(item_id), self.source
        except Exception as e:
            logger.error(f'Cannot retrieve secret value for id {item_id}: {e}')
            return None, self.source

    def prepare_new_masterkey(self) -> str:
        """Prepare a new master key for the secure store.

        Returns:
            str: The prepared master key string, or None if failed.
        """        
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

    def __init__(self, init_config:  Dict[str, str]):
        """Initialize a file-based value store.

        Args:
            init_config (Dict[str, str]): The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.CFGFILE)
        self.config_file = self.config._config_values.get(
            config_configfile.config_id).value
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
        config_section = self._get_cfg_def_value(item_id, str(CDF.SECTION))
        config_name = self._get_cfg_def_value(item_id, str(CDF.NAME))
        if config_section in self.configfile_content and config_name in self.configfile_content[config_section]:
            return self.configfile_content[config_section][config_name], self.source
        return None, self.source

    def save_value(self, item_id, value) -> bool:
        """Save a value to the YAML configuration file.

        Args:
            item_id (str): The configuration item identifier.
            value (Any): The value to store.

        Returns:
            bool: True if saved successfully, False otherwise.
        """        
        config_section = self._get_cfg_def_value(item_id, str(CDF.SECTION))
        config_name = self._get_cfg_def_value(item_id, str(CDF.NAME))
        if config_section not in self.configfile_content:
            self.configfile_content[config_section] = {}
        self.configfile_content[config_section][config_name] = value
        return self._write_configfile()

    def _write_configfile(self) -> bool:
        """Write the current configuration to the YAML file.

        Returns:
            bool: True if the file was written successfully, False otherwise.
        """        
        config_path = Path(self.config_file)
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
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


class ValueStoreEnv(ValueStore):
    """Value store that retrieves configuration values from environment variables."""
    
    def __init__(self, init_config:  Dict[str, str]):
        """Initialize an environment-variable-based value store.

        Args:
            init_config (Dict[str, str]): The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.ENV_VAR)

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieve a value from an environment variable.

        Args:
            item_id (str): The configuration item identifier.

        Returns:
            tuple[Any, str]: The retrieved value and its source type.
        """        
        config_env = self._get_cfg_def_value(item_id, str(CDF.ENV))
        if config_env is not None:
            return os.getenv(config_env), self.source
        return None, self.source


class ValueStoreDefault(ValueStore):
    """Value store that retrieves configuration default values."""
    
    def __init__(self, init_config:  Dict[str, str]):
        """Initialize a value store with default values.

        Args:
            init_config (Dict[str, str]): The configuration object that holds initialization values.
        """
        super().__init__(init_config, ConfigValueSource.DEFAULT)

    def retrieve_value(self, item_id: str) -> tuple[Any, str]:
        """Retrieve a default value from the configuration definition.

        Args:
            item_id (str): The configuration item identifier.

        Returns:
            tuple[Any, str]: The default value and its source type.
        """        
        config_default = self._get_cfg_def_value(item_id, str(CDF.DEFAULT))
        if config_default:
            return config_default, self.source
        return None, self.source


class ValueStores:
    """Factory and registry for initialized value store instances."""
        
    value_stores = {}

    @classmethod
    def get(cls, value_store_class: Type[ValueStore], init_config: Dict[str, str] = None):
        """Retrieve or initialize a value store instance.

        Args:
            value_store_class (Type[ValueStore]): The value store class to retrieve or initialize.
            init_config (Dict[str, str], optional): The initialization configuration. Required if the instance is not yet initialized.

        Returns:
            ValueStore: The initialized value store instance.

        Raises:
            ValueError: If the class is invalid or initialization fails.
        """        
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
