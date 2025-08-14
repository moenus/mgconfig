import logging


class ConstConfigs:
    _registry = {}  # name -> instance

    def __init__(self, name: str):
        self.name = name
        self.config_id = None
        # Register in dict
        self.__class__._registry[name] = self
        # Also register as class attribute
        setattr(self.__class__, name, self)

    @classmethod
    def get_config_id(cls, name):
        if name not in cls._registry:
            raise ValueError(f"Name {name} undefined.")

        cfg_obj = cls._registry[name]
        if cfg_obj.config_id is None:
            raise ValueError(f"Name {name} not initialized.")
        return cfg_obj.config_id


class SectionPrefix:
    def __init__(self):
        self.prefix = None

    def __str__(self):
        if self.prefix:
            return str(self.prefix)
        else:
            raise TypeError(f'Section prefix undefined.')

    def build_id(self, config_name):
        return str(self) + '_' + config_name


class ConstSections:
    APP = SectionPrefix()
    SEC = SectionPrefix()

    @classmethod
    def set_prefix(cls, section_handle, prefix):
        if section_handle in cls.__dict__:
            cls.__dict__[section_handle].prefix = prefix

    @classmethod
    def define(cls, section_handle):
        if not section_handle in cls.__dict__:
            setattr(cls, section_handle, SectionPrefix())


class LoggerWrapper:
    def __init__(self):
        # logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger("mgconf")
        self._logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    def replace_logger(self, logger):
        self._logger = logger

    def __getattr__(self, name):
        # delegate attribute access to the current logger
        return getattr(self._logger, name)       

logger = LoggerWrapper()
