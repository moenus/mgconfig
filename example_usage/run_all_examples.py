# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import mgconfig
import example_0_install_verify as example_0_install_verify

print(f"{'-'*30} example_1_basic {'-'*30} " )
import example_1_basic as example_1_basic

mgconfig.Configuration.reset_instance()
mgconfig.ConfigDefs.reset_instance()
print(f"{'-'*30} example_2_intermediate {'-'*30} " )
import example_2_intermediate as example_2_intermediate

mgconfig.Configuration.reset_instance()
mgconfig.ConfigDefs.reset_instance()
print(f"{'-'*30} example_3_advanced {'-'*30} " )
import example_3_advanced as example_3_advanced

mgconfig.Configuration.reset_instance()
mgconfig.ConfigDefs.reset_instance()
print(f"{'-'*30} example_4_extended {'-'*30} " )
import example_4_extended as example_4_extended
