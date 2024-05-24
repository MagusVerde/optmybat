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
