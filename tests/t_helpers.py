import os
from dotenv import load_dotenv
from mgconfig import secure_store
import shutil
from pathlib import Path
from mgconfig import Configuration, DefaultValues
from example_usage.ext_app_header import AppHeader

CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__test.yml"
]

root_dir = os.path.dirname(os.path.abspath(__file__))
test_basedir = Path(root_dir) / 'temp_basedir'

def prepare_new_env_master_key():
    os.environ["APP_KEY"] = secure_store.generate_key_str()

def prepare_clean_basedir():
    os.environ["DATA_DIRECTORY"] = test_basedir.as_posix()
    shutil.rmtree(test_basedir, ignore_errors=True)
    test_basedir.mkdir(exist_ok=True)
    return test_basedir


def get_test_filepath(filename):
    return Path(test_basedir) / filename


def set_app_header():
    DefaultValues().clear()
    AppHeader.name = 'testapp'
    AppHeader.title = 'Application Title'
    AppHeader.prefix = 'app'
    AppHeader.version = 'V1.0'


def create_configuration():
    set_app_header()
    return Configuration(CONFIG_DEFINITIONS_YAML)


# def load_development_env():
#     # used in development environments
#     DEVELOPMENT_ENV = Path(root_dir) / 'development.env'
#     if os.path.exists(DEVELOPMENT_ENV):
#         load_dotenv(dotenv_path=DEVELOPMENT_ENV)


def remove_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
