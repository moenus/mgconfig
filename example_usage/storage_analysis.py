# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import tracemalloc
from mgconfig import Configuration, DefaultValues
from mgconfig.config_defs import ConfigDefs
from mgconfig.config_value_handler import ConfigValueHandler
# from mgconfig.config_values import config_values
import gc,sys
from collections import Counter
from mgconfig import config_logger
import logging 


def count_objs(obj_list):
    gc.collect()  # run garbage collector
    all_objects = gc.get_objects()
    selected_types = [type(o).__name__ for o in all_objects if type(o).__name__ in obj_list]
    selected_objs = [o for o in all_objects if type(o).__name__ in obj_list]
    count_types = dict(Counter(selected_types))
    print(f'{'-'*40}')
    for obj in selected_objs:
        print(f'{type(obj).__name__ } - {obj} - {sys.getrefcount(obj)}')
        if type(obj).__name__ == "ConfigValue":
            print (obj.config_id)
    print(f'{count_types} - {len(selected_objs)}')


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__example.yml"
]

current_old = 0
DefaultValues().add('app_name', 'mgconfig_demo')
config_logger._logger.setLevel(logging.INFO)

def track_mem(label):
    global current_old
    gc.collect()  # run garbage collector
    current, peak_return = tracemalloc.get_traced_memory()
    print(f"{label} Current: {current / 1024:.2f} KB; Peak: {peak_return / 1024:.2f} KB; Delta: {(current - current_old) / 1024:.2f} KB")
    current_old = current

#--------------------------------------------------------------------------------------------------------------------------


tracemalloc.start()
track_mem('Start: ')


# ConfigDefs(CONFIG_DEFINITIONS_YAML)
# track_mem("CDef  :")

# ConfigDefs.reset_instance()
# track_mem("Reset  :")

# count_objs(["ConfigDef", "ConfigDefs", "DefDict", "CDF"])

# ConfigDefs(CONFIG_DEFINITIONS_YAML)
# track_mem("CDef  :")


# ConfigValueHandler.build()
# count_objs(["ConfigDef", "ConfigDefs", "ConfigValue"])

# config_values.clear()
# count_objs(["ConfigDef", "ConfigDefs", "ConfigValue"])

# pass


#--------------------------------------------------------------------------------------------------------------------------

print(f'{('-'*60) } config = Configuration(CONFIG_DEFINITIONS_YAML)')
config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")

count_objs(["Configuration", "ConfigDefs", "ConfigDef", "ConfigValue"])


# instance = Configuration()
# referrers = gc.get_referrers(instance)

# print(f"Number of references: {len(referrers)}")
# for i, ref in enumerate(referrers):
#     print(f"Referrer {i}: type={type(ref)}, repr={repr(ref)[:200]}")

# for ref in referrers:
#     if isinstance(ref, dict):
#         print("Dict keys:", list(ref.keys()))
#         # Optionally print where this dict is from
#     elif hasattr(ref, "__class__"):
#         print("Object:", type(ref), ref)

# instaance = None
# referrers = None        

# instance = config.get_config_object('host_hostname')

print(f'{('-'*60) } Configuration.reset_instance()')
# instance = config
del config
Configuration.reset_instance()
ConfigValueHandler.reset_values()
ConfigDefs.reset_instance()
track_mem("Reset: ")

count_objs(["Configuration", "ConfigDefs", "ConfigValue"])


# instance = Configuration()
# referrers = gc.get_referrers(instance)

# print(f"Number of references: {len(referrers)}")
# for i, ref in enumerate(referrers):
#     print(f"Referrer {i}: type={type(ref)}, repr={repr(ref)[:200]}")

# for ref in referrers:
#     if isinstance(ref, dict):
#         print("Dict keys:", list(ref.keys()))
#         # Optionally print where this dict is from
#     elif hasattr(ref, "__class__"):
#         print("Object:", type(ref), ref)

# instaance = None
# referrers = None 

# print(f'{('-'*60) } config = Configuration(CONFIG_DEFINITIONS_YAML)')
# config = Configuration(CONFIG_DEFINITIONS_YAML)
# track_mem("Config:")

# print(f'{('-'*60) } Configuration.reset_instance()')
# config = None
# Configuration.reset_instance()
# track_mem("Reset: ")

# config = Configuration(CONFIG_DEFINITIONS_YAML)
# track_mem("Config:")
