import mgconfig.extension_system
from mgconfig.helpers import ConstSections

class AppHeaderMeta(type):
    def __setattr__(cls, name, value):
        if name not in cls.__dict__:
            raise TypeError(f'Name {name} not defined in AppHeader.')
        # print(f"Intercepted setting {name} = {value!r} on class {cls.__name__}")
        super().__setattr__(name, value)
        mgconfig.extension_system.DefaultValues().add(ConstSections.APP.build_id(name), value)    

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
    
    # @classmethod
    # def set_as_default(cls):
    #     header = cls.get_header()
    #     for name in header:
    #         mgconfig.extension_system.DefaultValues().add(ConfigId.build(SectionPrefix.get(PREFIX_NAME_APP), name), header[name])