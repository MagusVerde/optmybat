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

import json
import pytest

from util.classyjson import ClassyJSON

def test_empty():
    '''
    Test the attributes of an empty ClassyJSON
    '''
    empty = ClassyJSON()
    assert len(empty) == 0
    assert len(vars(empty)) == 0
    empty = ClassyJSON("{}")
    assert len(empty) == 0
    assert len(vars(empty)) == 0

def test_initialiser():
    '''
    Test that we can initialise from a JSON string
    '''
    d = ClassyJSON('{"a": 1, "b": "a"}', c=True)
    assert len(d) == 3
    assert d['a'] == 1
    assert d['b'] == 'a'
    assert d['c']
    assert d.a == 1
    assert d.b == 'a'
    assert d.c

def test_toString():
    base = '{"a": 1, "b": 2}'
    d = ClassyJSON(base)
    assert str(d) == json.dumps(json.loads(base))
