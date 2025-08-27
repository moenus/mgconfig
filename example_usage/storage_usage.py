# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import tracemalloc
from mgconfig import Configuration, DefaultValues
from mgconfig.config_defs import ConfigDefs
import gc,sys
from collections import Counter
import objgraph


def free_memory():
    gc.collect()  # run garbage collector


def count_objs(obj_list):
    gc.collect()  # run garbage collector
    all_objects = gc.get_objects()
    selected_types = [type(o).__name__ for o in all_objects if type(o).__name__ in obj_list]
    selected_objs = [o for o in all_objects if type(o).__name__ in obj_list]
    count_types = dict(Counter(selected_types))
    print(f'{'-'*40}')
    for obj in selected_objs:
        print(f'{type(obj).__name__ } - {obj} - {sys.getrefcount(obj)}')
    print(f'{count_types} - {len(selected_objs)}')


CONFIG_DEFINITIONS_YAML = [
    "config_defs/config_def__app.yml",
    "config_defs/config_def__example.yml"
]

current_old = 0
DefaultValues().add('app_name', 'mgconfig_demo')

def track_mem(label):
    global current_old
    free_memory()
    current, peak_return = tracemalloc.get_traced_memory()
    print(f"{label} Current: {current / 1024:.2f} KB; Peak: {peak_return / 1024:.2f} KB; Delta: {(current - current_old) / 1024:.2f} KB")
    current_old = current

#--------------------------------------------------------------------------------------------------------------------------

tracemalloc.start()
track_mem('Start: ')


ConfigDefs(CONFIG_DEFINITIONS_YAML)
track_mem("CDef  :")

ConfigDefs.reset()
track_mem("Reset  :")

count_objs(["ConfigDef", "ConfigDefs", "DefDict", "CDF"])


ConfigDefs(CONFIG_DEFINITIONS_YAML)
track_mem("CDef  :")

config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")

count_objs(["Configuration", "ConfigDefs", "ConfigDef", "ConfigValue"])

objgraph.show_refs([config], filename='sample-graph.png')

instance = Configuration._instance
referrers = gc.get_referrers(instance)

print(f"Number of references: {len(referrers)}")
for i, ref in enumerate(referrers):
    print(f"Referrer {i}: type={type(ref)}, repr={repr(ref)[:200]}")

for ref in referrers:
    if isinstance(ref, dict):
        print("Dict keys:", list(ref.keys()))
        # Optionally print where this dict is from
    elif hasattr(ref, "__class__"):
        print("Object:", type(ref), ref)

instaance = None
referrers = None        

config = None
Configuration.reset()
track_mem("Reset: ")

count_objs(["Configuration", "ConfigDefs", "ConfigValue"])

objgraph.show_most_common_types() 

# instance = Configuration._instance
# referrers = gc.get_referrers(instance)

# # print(f"Number of references: {len(referrers)}")
# # for i, ref in enumerate(referrers):
# #     print(f"Referrer {i}: type={type(ref)}, repr={repr(ref)[:200]}")

# for ref in referrers:
#     if isinstance(ref, dict):
#         print("Dict keys:", list(ref.keys()))
#         # Optionally print where this dict is from
#     elif hasattr(ref, "__class__"):
#         print("Object:", type(ref), ref)

config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")

Configuration.reset()
track_mem("Reset: ")

config = Configuration(CONFIG_DEFINITIONS_YAML)
track_mem("Config:")
