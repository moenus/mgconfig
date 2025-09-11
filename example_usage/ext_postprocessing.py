# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import pytz

LOCAL_TZ_ID = 'local_tz'
HOST_TIMEZONE_ID = 'host_timezone'

def extend_timezone_configuration(conf):
    host_timezone = conf.get_value(HOST_TIMEZONE_ID)
    if host_timezone:
        value = pytz.timezone(host_timezone)
        conf.set_property_value(LOCAL_TZ_ID, value)
        