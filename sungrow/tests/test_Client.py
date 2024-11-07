#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Tests of the extended client.  Note that some of these tests will fail
# unless your configuration is correct.
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
import time

from sungrow.client import Client
from sungrow.support import SungrowError

def testBadHost():
    '''
    Test that things fail properly if given a bad host
    '''
    with pytest.raises(SungrowError):
        client = Client(host='127.0.0.1')

def testConnect():
    '''
    Test that we can properly init the client.
    '''
    client = Client()
    assert client.ws_socket is not None
    assert client.ws_token
    r = client.get("/time/get")
    assert r.time
    client.close()
    time.sleep(1)
    assert client.ws_socket is None
    assert not client.ws_token
