#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Definitions of the known, important SH5 inverter parameters
#
# This file is part of Optmybat.
#
# Optmybat is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Optmybat is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# NO AI TRAINING: Any use of this code related to the development, or training
# of AI systems is explicitly prohibited. Personal use, indexing for Internet
# search engines, etc. is intended, permitted and encouraged.
#
# You can review the GNU Affero General Public License at <https://www.gnu.org/licenses/>.

from sungrow.parameters import Register

#-----------------------------------------------------------------
# The param_addr values for the parameters that control force charging.
# These could easily be loaded from a config file rather than hard coded.
SH5_FORCE_CHARGE_PARAM_MAP = {
    'fc_enable': 33208,
    'fc_weekdays_only': 33209,
    'fc1_start_hr': 33210,
    'fc1_start_min': 33211,
    'fc1_end_hr': 33212,
    'fc1_end_min': 33213,
    'fc1_soc': 33214,
    'fc2_start_hr': 33215,
    'fc2_start_min': 33216,
    'fc2_end_hr': 33217,
    'fc2_end_min': 33218,
    'fc2_soc': 33219,
}

SH5_FORCE_CHARGE_PARAMS = {
    'em_mode': Register('em_mode', id=1, addr=33146, type=1, pname="I18N_COMMON_ENERGY_MANAGEMENT_MODE"),
    'fc_enable': Register('fc_enable', id=21, addr=33208, type=1, pname="I18N_COMMON_FORCED_CHARGE_ENABLE"),
    'fc_weekdays_only': Register('fc_weekdays_only', id=22, addr=33209, type=1, pname="I18N_COMMON_VALITETIME"),
    'fc1_start_hr': Register('fc1_start_hr', id=23, addr=33210, type=2, pname="I18N_CONFIG_KEY_2808"),
    'fc1_start_min': Register('fc1_start_min', id=24, addr=33211, type=2, pname="I18N_CONFIG_KEY_2807"),
    'fc1_end_hr': Register('fc1_end_hr', id=25, addr=33212, type=2, pname="I18N_CONFIG_KEY_2804"),
    'fc1_end_min': Register('fc1_end_min', id=26, addr=33213, type=2, pname="I18N_CONFIG_KEY_2803"),
    'fc1_soc': Register('fc1_soc', id=27, addr=33214, type=2, pname="I18N_CONFIG_KEY_2801"),
    'fc2_start_hr': Register('fc2_start_hr', id=28, addr=33215, type=2, pname="I18N_CONFIG_KEY_2810"),
    'fc2_start_min': Register('fc2_start_min', id=29, addr=33216, type=2, pname="I18N_CONFIG_KEY_2809"),
    'fc2_end_hr': Register('fc2_end_hr', id=30, addr=33217, type=2, pname="I18N_CONFIG_KEY_2806"),
    'fc2_end_min': Register('fc2_end_min', id=31, addr=33218, type=2, pname="I18N_CONFIG_KEY_2805"),
    'fc2_soc': Register('fc2_soc', id=32, addr=33219, type=2, pname="I18N_CONFIG_KEY_2802"),
}

SH5_REALTIME_POWER_MAP = {
    "I18N_COMMON_TOTAL_BACKUP_POWER_WLECIVPM": "total_backup_power",
    "I18N_COMMON_TOTAL_APPARENT_POWER": "total_apparent_power",
    "I18N_COMMON_TOTAL_REACTIVE_POWER": "total_reactive_power",
    "I18N_COMMON_TOTAL_ACTIVE_POWER": "total_active_power",
    "I18N_COMMON_TOTAL_DCPOWER": "total_dc_power",
    "I18N_COMMON_LOAD_TOTAL_ACTIVE_POWER": "load_total_active_power",
    "I18N_CONFIG_KEY_4060": "purchased_power",
    "I18N_COMMON_FEED_NETWORK_TOTAL_ACTIVE_POWER": "feed_power"
}

#-----------------------------------------------------------------
# Map Sungrow battery data names to our internal property names.
# See client.getBatteryInfo().
SH5_BATTERY_PROPERTY_MAP = {
    "I18N_CONFIG_KEY_3907": "charge_kw",
    "I18N_CONFIG_KEY_3921": "discharge_kw",
    "I18N_COMMON_BATTERY_TEMPERATURE": "temperature",
    "I18N_COMMON_BATTERY_SOC": "soc",
    "I18N_COMMON_BATTARY_HEALTH": "health"
}
