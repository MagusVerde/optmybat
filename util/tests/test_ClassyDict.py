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

from util.classydict import ClassyDict

def test_emptyDict():
    '''
    Test the attributes of an empty ClassyDict
    '''
    empty = ClassyDict()
    assert len(empty) == 0
    assert len(vars(empty)) == 0

def test_initialiser():
    '''
    Test that we can initialise from a dict and things work as expected
    '''
    d = ClassyDict({'a': 1, 'b': 2})
    assert len(d) == 2
    assert d['a'] == 1
    assert d['b'] == 2
    assert d.a == 1
    assert d.b == 2

def test_exceptions():
    '''
    Test that we get the expected exceptions
    '''
    empty = ClassyDict()
    with pytest.raises(KeyError) as e:
        print(empty['a'])
    with pytest.raises(AttributeError) as e:
        print(empty.a)

def test_contains():
    d = ClassyDict()
    d['a'] = 1
    assert 'a' in d
    assert 'b' not in d

def test_hasattr():
    d = ClassyDict()
    d['a'] = 1
    assert hasattr(d, 'a'), f"hasattr returned False for an existing attribute"
    assert not hasattr(d, 'b'), f"hasattr returned True for a missing attribute"

def test_gettter_setter():
    d = ClassyDict()
    d['a'] = 1
    assert d.a == 1
    d.b = 2
    assert d['b'] == 2
    d.c = d.b = 3
    assert d['c'] == 3
    d['c'] = d.a = -1
    assert d['c'] == -1

def test_del():
    d = ClassyDict({'a': 1, 'b': 2})
    del(d.a)
    assert len(d) == 1
    assert not hasattr(d, 'a')
    assert hasattr(d, 'b')
    del(d['b'])
    assert len(d) == 0

def test_jsonDump():
    base = {'a': 1, 'b': 2}
    d = ClassyDict(base)
    assert json.dumps(d) == json.dumps(base)

def testPrivateAttribues():
    # Populate with some public and private items
    base = {'a': 1, '_private': 3}
    obj = ClassyDict(base)
    obj._secret = 'ssshhh'
    obj['__super_secret'] = 'nope'
    # Check that the private items aren't included in len(), etc
    assert len(obj) == 1
    assert repr(obj) == "ClassyDict({'a': 1})"
    assert str(obj) == "{'a': 1}"
    assert list(obj.keys()) == ['a']
    assert list(obj.items()) == [('a', 1)]
    assert '_private' not in obj
    # Check that the private variables are accessable
    assert obj._private == 3
    assert obj['_private'] == 3
    assert obj._secret == 'ssshhh'
    assert obj['_secret'] == 'ssshhh'
    assert obj.__super_secret == 'nope'
    assert obj['__super_secret'] == 'nope'
    # Check that private variables can be deleted
    assert hasattr(obj, '_secret')
    del(obj._secret)
    assert not hasattr(obj, '_secret')
    assert obj.get('_secret', None) == None
    assert hasattr(obj, '_private')
    del(obj['_private'])
    assert not hasattr(obj, '_private')
    assert obj.get('_private', None) == None
