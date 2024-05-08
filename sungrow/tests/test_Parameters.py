#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Tests the Parameters and Register classes.
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

import pytest

from sungrow.parameters import Parameters, Register

#---------------------------------------------------------------------
# Constants for testing

TEST_PARAM_LIST = [
        {
            "param_id": 4,
            "param_addr": 1,
            "param_pid": -1,
            "param_type": 2,
            "accuracy": 0,
            "param_name": "I18N_CONFIG_KEY_2620",
            "param_value": "1",
            "unit": "h",
            "relation": "",
            "regulation": "",
            "range": "[0~23]",
            "options": ""
        },
        {
            "param_id": 2,
            "param_addr": 2,
            "param_pid": -1,
            "param_type": 2,
            "accuracy": 0,
            "param_name": "I18N_CONFIG_KEY_2619",
            "param_value": "2",
            "unit": "min",
            "relation": "",
            "regulation": "",
            "range": "[0~59]",
            "options": ""
        },
        {
            "param_id": 3,
            "param_addr": 3,
            "param_pid": -1,
            "param_type": 2,
            "accuracy": 0,
            "param_name": "I18N_CONFIG_KEY_2616",
            "param_value": "3",
            "unit": "h",
            "relation": "",
            "regulation": "",
            "range": "[0~24]",
            "options": ""
        },
        {
            "param_id": 4,
            "param_addr": 4,
            "param_pid": -1,
            "param_type": 2,
            "accuracy": 0,
            "param_name": "I18N_CONFIG_KEY_2615",
            "param_value": "4",
            "unit": "min&I18N_COMMON_PARAMS_SETTING_TIP",
            "relation": "",
            "regulation": "",
            "range": "[0~59]",
            "options": ""
        }
]

def test_parsing():
    params = Parameters({1: Register('one'), 3: Register('three'), 53: Register('fifty3')})
    params.parse(TEST_PARAM_LIST)
    assert len(params) == 2
    assert params.one.addr == 1
    assert params.three.addr == 3

def test_update():
    params = Parameters({1: Register('one'), 3: Register('three'), 53: Register('fifty3')})
    params.parse(TEST_PARAM_LIST)
    assert params.one.value == '1'
    params.one.value = 12
    assert params.one.value == 12

def test_addressMap():
    params = Parameters()
    params.loadAddressMap({'param3': 3, 'four': 4})
    params.parse(TEST_PARAM_LIST)
    assert len(params) == 2
    assert params.param3.addr == 3
    assert params.four.addr == 4
