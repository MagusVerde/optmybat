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

import pytest

from sungrow.support import TimedTarget

# A bunch of tests for the TimedTarget._loadTargets() method
def test_simple_targets():
    '''
    Test that TimedTarget.loadTargets correctly handles simple cases
    '''
    # Can it handle an empty list
    r = TimedTarget.loadTargets([])
    assert len(r) == 0
    # Does it correctly parse a single entry
    t1_dict = {'start': '00:00', 'stop': '06:00', 'target': 20}
    t1_target = TimedTarget('00:00', '06:00', 20)
    r = TimedTarget.loadTargets([t1_dict])
    assert len(r) == 1
    assert r[0] == t1_target
    assert r[0].target == t1_target.target
    # Another single entry
    t1_dict = {'start': '00:00', 'stop': '24:00', 'target': 20}
    t1_target = TimedTarget('00:00', '24:00', 20)
    r = TimedTarget.loadTargets([t1_dict])
    assert len(r) == 1
    assert r[0] == t1_target
    assert r[0].target == t1_target.target
    # Does it correctly parse a wrapped entry
    wrapped_dict = {'start': '23:00', 'stop': '06:00', 'target': 20}
    wrapped1 = TimedTarget('00:00', '06:00', 20)
    wrapped2 = TimedTarget('23:00', '00:00', 20)
    r = TimedTarget.loadTargets([wrapped_dict])
    assert len(r) == 2
    assert r[0] == wrapped1
    assert r[0].target == wrapped1.target
    assert r[1] == wrapped2
    assert r[1].target == wrapped2.target

def test_overlap_1():
    '''
    Test that TimedTarget.loadTargets correctly handles two identical times.
    '''
    # No overlap at all
    overlap = [
        {'start': '05:00', 'stop': '06:00', 'target': 20},
        {'start': '06:00', 'stop': '08:00', 'target': 5}
    ]
    c1 = TimedTarget('05:00', '06:00', 20)
    c2 = TimedTarget('06:00', '08:00', 5)
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == 2
    assert r[0] == c1
    assert r[0].target == c1.target
    assert r[1] == c2
    assert r[1].target == c2.target
    # A simple overlap
    overlap = [
        {'start': '05:00', 'stop': '06:00', 'target': 20},
        {'start': '05:00', 'stop': '06:00', 'target': 5}
    ]
    c = TimedTarget('05:00', '06:00', 20)
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == 1
    assert r[0] == c
    assert r[0].target == c.target

def test_overlap_2():
    '''
    Test that TimedTarget.loadTargets correctly handles overlaps
    where one time is completely inside another.
    '''
    # A fairly simple overlap
    overlap = [
        {'start': '00:00', 'stop': '06:00', 'target': 20},
        {'start': '02:00', 'stop': '04:00', 'target': 5},
    ]
    c = TimedTarget('00:00', '06:00', 20)
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == 1
    assert r[0] == c
    assert r[0].target == c.target
    # A more complex overlap
    overlap = [
        {'start': '00:00', 'stop': '06:00', 'target': 5},
        {'start': '02:00', 'stop': '04:00', 'target': 20},
    ]
    c1 = TimedTarget('00:00', '02:00', 5)
    c2 = TimedTarget('02:00', '04:00', 20)
    c3 = TimedTarget('04:00', '06:00', 5)
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == 3
    assert r[0] == c1
    assert r[0].target == c1.target
    assert r[1] == c2
    assert r[1].target == c2.target
    assert r[2] == c3
    assert r[2].target == c3.target

def test_overlap_3():
    '''
    Test that TimedTarget.loadTargets correctly handles overlaps
    where the stop times overlap.
    '''
    # t1 overrides t2
    overlap = [
        {'start': '00:00', 'stop': '06:00', 'target': 20},
        {'start': '02:00', 'stop': '08:00', 'target': 5},
    ]
    c1 = TimedTarget('00:00', '06:00', 20)
    c2 = TimedTarget('06:00', '08:00', 5)
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == 2
    assert r[0] == c1
    assert r[0].target == c1.target
    assert r[1] == c2
    assert r[1].target == c2.target
    # t2 overrides t1
    overlap = [
        {'start': '00:00', 'stop': '06:00', 'target': 5},
        {'start': '02:00', 'stop': '08:00', 'target': 20},
    ]
    c1 = TimedTarget('00:00', '02:00', 5)
    c2 = TimedTarget('02:00', '08:00', 20)
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == 2
    assert r[0] == c1
    assert r[0].target == c1.target
    assert r[1] == c2
    assert r[1].target == c2.target

def test_overlap_4():
    overlap = [
        {'start': '23:00', 'stop': '06:00', 'target': 20},
        {'start': '05:00', 'stop': '13:00', 'target': 55},
        {'start': '00:00', 'stop': '24:00', 'target': 5},
        {'start': '11:00', 'stop': '16:00', 'target': 30},
        {'start': '15:00', 'stop': '18:00', 'target': 25}
    ]
    expected = [
        TimedTarget('00:00', '05:00', 20),
        TimedTarget('05:00', '13:00', 55),
        TimedTarget('13:00', '16:00', 30),
        TimedTarget('16:00', '18:00', 25),
        TimedTarget('18:00', '23:00', 5),
        TimedTarget('23:00', '24:00', 20),
    ]
    r = TimedTarget.loadTargets(overlap)
    assert len(r) == len(expected)
    for i in range(len(r)):
        assert r[i] == expected[i]
        assert r[i].target == expected[i].target
