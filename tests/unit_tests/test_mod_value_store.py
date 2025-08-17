import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import yaml

# Import the module under test
import mgconfig.value_store as mod


class TestValueStoreFile(unittest.TestCase):

    def setUp(self):
        self.init_config = MagicMock()
        self.init_config._config_values = {
            mod.config_configfile.config_id: MagicMock(value="config.yaml")
        }
        self.init_config._cfg_def_dict = {
            "test_item": {
                str(mod.CDF.SECTION): "section1",
                str(mod.CDF.NAME): "name1"
            }
        }

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="section1:\n  name1: value1")
    def test_read_configfile_exists(self, mock_file, mock_exists):
        store = mod.ValueStoreFile(self.init_config)
        self.assertEqual(store.configfile_content, {
                         "section1": {"name1": "value1"}})
        mock_file.assert_called_once_with("config.yaml", "r")

    @patch("os.path.exists", return_value=False)
    def test_read_configfile_missing(self, mock_exists):
        store = mod.ValueStoreFile(self.init_config)
        self.assertEqual(store.configfile_content, {})

    def test_retrieve_value_found(self):
        store = mod.ValueStoreFile(self.init_config)
        store.configfile_content = {"section1": {"name1": "value1"}}
        val, src = store.retrieve_value("test_item")
        self.assertEqual(val, "value1")
        self.assertEqual(src, mod.ConfigValueSource.CFGFILE)

    def test_retrieve_value_not_found(self):
        store = mod.ValueStoreFile(self.init_config)
        store.configfile_content = {}
        val, src = store.retrieve_value("test_item")
        self.assertIsNone(val)
        self.assertEqual(src, mod.ConfigValueSource.CFGFILE)

    @patch("builtins.open", new_callable=mock_open)
    @patch.object(Path, "mkdir")
    def test_save_value_and_write_success(self, mock_mkdir, mock_file):
        store = mod.ValueStoreFile(self.init_config)
        store.configfile_content = {}
        with patch("yaml.dump") as mock_dump:
            result = store.save_value("test_item", "new_value")
        self.assertTrue(result)
        mock_dump.assert_called_once()

    @patch("builtins.open", side_effect=OSError("write error"))
    @patch.object(Path, "mkdir")
    def test_write_configfile_failure(self, mock_mkdir, mock_file):
        store = mod.ValueStoreFile(self.init_config)
        store.configfile_content = {}
        result = store._write_configfile()
        self.assertFalse(result)


class TestValueStoreEnv(unittest.TestCase):

    def setUp(self):
        self.init_config = MagicMock()
        self.init_config._cfg_def_dict = {
            "item1": {str(mod.CDF.ENV): "MY_ENV_VAR"}
        }

    @patch.dict(os.environ, {"MY_ENV_VAR": "123"})
    def test_retrieve_value_exists(self):
        store = mod.ValueStoreEnv(self.init_config)
        val, src = store.retrieve_value("item1")
        self.assertEqual(val, "123")
        self.assertEqual(src, mod.ConfigValueSource.ENV_VAR)

    @patch.dict(os.environ, {}, clear=True)
    def test_retrieve_value_missing(self):
        store = mod.ValueStoreEnv(self.init_config)
        val, src = store.retrieve_value("item1")
        self.assertIsNone(val)
        self.assertEqual(src, mod.ConfigValueSource.ENV_VAR)


class TestValueStoreDefault(unittest.TestCase):

    def setUp(self):
        self.init_config = MagicMock()
        self.init_config._cfg_def_dict = {
            "item1": {str(mod.CDF.DEFAULT): "default_value"}
        }

    def test_retrieve_value_exists(self):
        store = mod.ValueStoreDefault(self.init_config)
        val, src = store.retrieve_value("item1")
        self.assertEqual(val, "default_value")
        self.assertEqual(src, mod.ConfigValueSource.DEFAULT)

    def test_retrieve_value_missing(self):
        self.init_config._cfg_def_dict = {"item1": {}}
        store = mod.ValueStoreDefault(self.init_config)
        val, src = store.retrieve_value("item1")
        self.assertIsNone(val)


class TestValueStoreSecure(unittest.TestCase):

    def setUp(self):
        # Common init_config mock
        self.init_config = MagicMock()
        self.init_config.get.return_value = "securestore_file"
        self.init_config._cfg_def_dict = {}

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore")
    def test_init_and_validate_masterkey(self, mock_secure_store, mock_key_provider):
        # Make constructor succeed
        mock_secure_store.return_value.validate_master_key.return_value = True

        store = mod.ValueStoreSecure(self.init_config)

        self.assertEqual(store.source, mod.ConfigValueSource.SECRET)
        mock_key_provider.assert_called_once_with(self.init_config)
        mock_secure_store.assert_called_once_with(
            "securestore_file", mock_key_provider.return_value
        )

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore")
    def test_save_value_success(self, mock_secure_store, mock_key_provider):
        # Prevent __init__ from failing
        mock_secure_store.return_value.validate_master_key.return_value = True
        store = mod.ValueStoreSecure(self.init_config)

        result = store.save_value("item1", "secret_value")

        self.assertTrue(result)
        mock_secure_store.return_value.store_secret.assert_called_with(
            "item1", "secret_value")
        mock_secure_store.return_value.save_securestore.assert_called_once()

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore", side_effect=OSError("cannot open"))
    def test_save_value_failure(self, mock_secure_store, mock_key_provider):
        # This fails already in save_value() because SecureStore() raises
        store = mod.ValueStoreSecure(self.init_config)
        result = store.save_value("item1", "secret_value")
        self.assertFalse(result)

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore")
    def test_retrieve_value_success(self, mock_secure_store, mock_key_provider):
        mock_secure_store.return_value.validate_master_key.return_value = True
        mock_secure_store.return_value.retrieve_secret.return_value = "secret_value"

        store = mod.ValueStoreSecure(self.init_config)
        val, src = store.retrieve_value("item1")

        self.assertEqual(val, "secret_value")
        self.assertEqual(src, mod.ConfigValueSource.SECRET)

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore", side_effect=OSError("cannot open"))
    def test_retrieve_value_failure(self, mock_secure_store, mock_key_provider):
        store = mod.ValueStoreSecure(self.init_config)
        val, src = store.retrieve_value("item1")

        self.assertIsNone(val)
        self.assertEqual(src, mod.ConfigValueSource.SECRET)

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore")
    def test_prepare_new_masterkey_success(self, mock_secure_store, mock_key_provider):
        mock_secure_store.return_value.validate_master_key.return_value = True
        mock_secure_store.return_value.prepare_auto_key_exchange.return_value = "newkey123"

        store = mod.ValueStoreSecure(self.init_config)
        result = store.prepare_new_masterkey()

        self.assertEqual(result, "newkey123")
        mock_secure_store.return_value.prepare_auto_key_exchange.assert_called_once()

    @patch.object(mod, "KeyProvider")
    @patch.object(mod, "SecureStore", side_effect=OSError("cannot open"))
    def test_prepare_new_masterkey_failure(self, mock_secure_store, mock_key_provider):
        store = mod.ValueStoreSecure(self.init_config)
        result = store.prepare_new_masterkey()
        self.assertIsNone(result)


class TestValueStoresFactory(unittest.TestCase):

    def test_get_existing_instance(self):
        mock_store = MagicMock()
        mod.ValueStores.value_stores = {mod.ValueStoreFile: mock_store}
        result = mod.ValueStores.get(mod.ValueStoreFile)
        self.assertEqual(result, mock_store)

    def test_get_invalid_class(self):
        with self.assertRaises(ValueError):
            mod.ValueStores.get(str, {})

    def test_get_without_init_config(self):
        with self.assertRaises(ValueError):
            mod.ValueStores.get(mod.ValueStoreFile)

    def test_get_creates_new_instance(self):
        class DummyStore(mod.ValueStore):
            def __init__(self, init_config):
                # minimal valid init
                super().__init__(init_config, mod.ConfigValueSource.CFGFILE)

        mod.ValueStores.value_stores.clear()
        cfg = {"any": "thing"}

        inst = mod.ValueStores.get(DummyStore, cfg)

        self.assertIsInstance(inst, DummyStore)
        # cached for next time
        self.assertIs(mod.ValueStores.value_stores[DummyStore], inst)

    def test_get_initialization_failure(self):
        class FailingStore(mod.ValueStore):
            def __init__(self, init_config):
                # simulate constructor failure
                raise RuntimeError("boom")

        mod.ValueStores.value_stores.clear()

        with self.assertRaises(ValueError) as ctx:
            mod.ValueStores.get(FailingStore, {"x": 1})

        self.assertIn("Cannot initialize value store", str(ctx.exception))
        self.assertNotIn(FailingStore, mod.ValueStores.value_stores)


if __name__ == "__main__":
    unittest.main()
