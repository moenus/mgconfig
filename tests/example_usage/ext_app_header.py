import mgconfig.extension_system
from mgconfig.helpers import section_APP, lazy_build_config_id

class AppHeaderMeta(type):
    def __setattr__(cls, name, value):
        if name not in cls.__dict__:
            raise TypeError(f'Name {name} not defined in AppHeader.')
        # print(f"Intercepted setting {name} = {value!r} on class {cls.__name__}")
        super().__setattr__(name, value)
        config_id = lazy_build_config_id(section_APP, name)
        mgconfig.extension_system.DefaultValues().add(config_id, value)    

class AppHeader(metaclass=AppHeaderMeta):
    name = None
    title = None
    prefix = None
    version = None

    def __init__(self):
        raise TypeError(f"{self.__class__.__name__} cannot be instantiated")

    @classmethod
    def get_header(cls):
        header = {}
        for name in cls.__dict__:
            if not name.startswith("_") and type(cls.__dict__[name]) == str:
                header[name] = cls.__dict__[name]
        return header
