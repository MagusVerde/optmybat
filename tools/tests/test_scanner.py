#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# A support module for Optmybat that supports network scanning to find
# and identify supported devices on the network.
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
import sys

from tools import scanner

def test_getNetwork():
    '''
    Simply checks that the call doesn't throw an exception
    '''
    networks = scanner.getNetworkDetails()

def test_tcpPing():
    '''
    Simply checks that the call doesn't throw an exception
    '''
    networks = scanner.getNetworkDetails()
    address = networks[0].addr
    if scanner.tcpPing(address, 80):
        desc = "does"
    else:
        desc = "does not"
    print(f"{address} {desc} have a web server")

def test_tcpScan():
    '''
    Simply checks that the call doesn't throw an exception
    '''
    networks = scanner.getNetworkDetails()
    net = networks[0].addr + "/" + networks[0].netmask
    found = scanner.tcpScan(net, 80)
    print(f"There are web servers on {','.join(found)}")

def test_sungrowScan():
    '''
    Mainly checks that the call doesn't throw an exception
    '''
    found = scanner.sungrowScan('127.1.1.0/24')
    assert(len(found) == 0)
