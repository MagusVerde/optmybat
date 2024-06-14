#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
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

import os
import pytest
import time

from util.config import Config

def test_singleton():
    '''
    Test that it's truly a singleton.
    '''
    Config.unload()
    c1 = Config.load()
    c2 = Config.load()
    Config.unload()
    assert c1 == c2

def test_update(tmpdir):
    '''
    Test that update detection is working.
    '''
    Config.unload()
    config = f"{tmpdir}/config.yml"
    with open(config, 'w') as cfd:
        cfd.write("admin_passwd: freaky")
    saved = os.environ.get('SH5_CONFIG', None)
    os.environ['SH5_CONFIG'] = config
    c1 = Config.load()
    if saved is not None:
        os.environ['SH5_CONFIG'] = saved
    assert c1.admin_passwd == 'freaky'
    time.sleep(1)
    with open(config, 'w') as cfd:
        cfd.write("admin_passwd: frosty")
    c2 = Config.load()
    Config.unload()
    assert c2.admin_passwd == 'frosty'

def test_config_path():
    '''
    Tests that config obeys the SH5_CONFIG environ variable.
    '''
    Config.unload()
    saved = os.environ.get('SH5_CONFIG', None)
    os.environ['SH5_CONFIG'] = ''
    c = Config.load()
    if saved is not None:
        os.environ['SH5_CONFIG'] = saved
    Config.unload()
    assert c.admin_user == 'user'
    assert c.admin_passwd == 'pw1111'
