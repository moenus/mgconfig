# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import tracemalloc
from mgconfig import Configuration, DefaultValues
from mgconfig.config_defs import ConfigDefs
from mgconfig.config_item_handler import ConfigItemHandler
import gc
import sys
from collections import Counter


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__example.yml"
]

current_old = 0
DefaultValues().add('app_name', 'mgconfig_demo')


def count_objs(obj_list):
    gc.collect()  # run garbage collector
    all_objects = gc.get_objects()
    selected_types = [
        type(o).__name__ for o in all_objects if type(o).__name__ in obj_list]
    selected_objs = [o for o in all_objects if type(o).__name__ in obj_list]
    count_types = dict(Counter(selected_types))
    print(f'{'-'*40}')
    for obj in selected_objs:
        print(f'{type(obj).__name__} - {obj} - {sys.getrefcount(obj)}  {obj.config_id if type(obj).__name__ == "ConfigValue" else ""}')

    print(f'{count_types} - {len(selected_objs)}')


def show_references(instance):
    referrers = gc.get_referrers(instance)
    print(f"Number of references: {len(referrers)}")
    for i, ref in enumerate(referrers):
        print(f"--> Referrer {i}: type={type(ref)}, repr={repr(ref)[:200]}")

    for ref in referrers:
        if isinstance(ref, dict):
            print("Dict keys:", list(ref.keys()))
            # Optionally print where this dict is from
        elif hasattr(ref, "__class__"):
            print("Object:", type(ref), ref)
    referrers = None


def track_mem(label):
    global current_old
    gc.collect()  # run garbage collector
    current, peak_return = tracemalloc.get_traced_memory()
    print(f"{label} Current: {current / 1024:.2f} KB; Peak: {peak_return / 1024:.2f} KB; Delta: {(current - current_old) / 1024:.2f} KB")
    current_old = current

# --------------------------------------------------------------------------------------------------------------------------


tracemalloc.start()
track_mem('Start: ')


ConfigDefs(CONFIG_DEFINITIONS_YAML)
track_mem("CDef  :")

ConfigDefs.reset_instance()
track_mem("Reset  :")

count_objs(["ConfigDef", "ConfigDefs", "DefDict", "CDF"])

ConfigDefs(CONFIG_DEFINITIONS_YAML)
track_mem("CDef  :")


ConfigItemHandler.build()
count_objs(["ConfigDef", "ConfigDefs", "ConfigValue"])


# --------------------------------------------------------------------------------------------------------------------------

print(f'{('-'*60)} config = Configuration(CONFIG_DEFINITIONS_YAML)')
config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")

count_objs(["Configuration", "ConfigDefs", "ConfigDef", "ConfigValue"])

show_references(config)

print(f'{('-'*60)} Configuration.reset_instance()')
del config
Configuration.reset_instance()
ConfigItemHandler.reset_values()
ConfigDefs.reset_instance()
track_mem("Reset: ")

count_objs(["Configuration", "ConfigDefs", "ConfigDef", "ConfigValue"])

print(f'{('-'*60) } config = Configuration(CONFIG_DEFINITIONS_YAML)')
config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")

print(f'{('-'*60) } Configuration.reset_instance()')
config = None
Configuration.reset_instance()
track_mem("Reset: ")

config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")
