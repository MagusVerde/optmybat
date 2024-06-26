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

from datetime import datetime
from util.config import Config
import pytest

from util.hhmmtime import HHMMTime

def test_new():
    '''
    Test that we can create new HHMMTimes
    '''
    t = HHMMTime(0)
    assert t.value == 0
    assert t.hours == 0
    assert t.minutes == 0
    t = HHMMTime('00:00')
    assert t.value == 0
    assert t.hours == 0
    assert t.minutes == 0
    t = HHMMTime(HHMMTime.ONE_DAY)
    assert t.value == 24 * 60
    assert t.hours == 24
    assert t.minutes == 0
    t = HHMMTime(24, 0)
    assert t.value == 24 * 60
    assert t.hours == 24
    assert t.minutes == 0
    t = HHMMTime(-1)
    assert t.value == 24 * 60 - 1
    assert t.hours == 23
    assert t.minutes == 59
    t = HHMMTime('11:30')
    assert t.value == 11 * 60 + 30
    assert t.hours == 11
    assert t.minutes == 30
    now = datetime.now(tz=Config.load().timezone)
    hm_now = HHMMTime.now()
    assert hm_now.hours == now.hour
    assert hm_now.minutes == now.minute

def test_arithmetic():
    '''
    Adding and subtracting times
    '''
    t = HHMMTime('00:00')
    t += 1
    assert t.value == 1
    assert t.hours == 0
    assert t.minutes == 1
    t -= 31
    assert t.value == 24 * 60 - 30
    assert t.hours == 23
    assert t.minutes == 30
    t += 60
    assert t.value == 30
    assert t.hours == 0
    assert t.minutes == 30
    t += '23:30'
    assert t.value == 0
    assert t.hours == 0
    assert t.minutes == 0
    a = -1
    t += a
    assert t.value == 24 * 60 - 1
    assert t.hours == 23
    assert t.minutes == 59
    t -= a
    assert t.value == 0
    assert t.hours == 0
    assert t.minutes == 0

def test_comparison():
    '''
    Test the comparison operators
    '''
    t1 = HHMMTime('11:45')
    t2 = HHMMTime('12:00')
    assert t1 != t2
    assert t1 < t2
    assert t2 > t1
    assert (t1 + 15) <= t2
    assert (t1 + 15) == t2
    assert (t1 + 15) >= t2
    t1 = HHMMTime('00:00')
    t2 = HHMMTime('24:00')
    assert t1 == t2
    assert t2 == t1
    assert t1 < t2
    assert t2 > t1
    # Check for a very corner case
    assert t1 <= t2
    assert t1 >= t2

def test_corners():
    '''
    Test all of the corner cases inherent in the design.  This replicates
    some of the other tests but it also serves to document the deliberate
    design behaviours.
    '''
    # Check that we can create 24:00
    assert HHMMTime('24:00').hours == 24
    assert HHMMTime(24, 0).hours == 24
    assert HHMMTime(HHMMTime.ONE_DAY).hours == 24
    # Check that, if we try to create 24:01, we get 00:01
    t = HHMMTime(HHMMTime.ONE_DAY+1)
    assert t.hours == 0 and t.minutes == 1
    # Check that 00:00 and 24:00 are distinct but equivalent
    midnight0 = HHMMTime(0)
    midnight24 = HHMMTime(HHMMTime.ONE_DAY)
    assert midnight0 ==  midnight24
    assert midnight0 < midnight24
    assert midnight24 > midnight0
    # The following tests all, somewhat counter intuitively, pass
    # because midnight0 ==  midnight24
    assert midnight0 >= midnight24
    assert midnight0 <= midnight24
    assert midnight24 >= midnight0
    assert midnight24 <= midnight0
    # Check that doing arithmetic around 00:00 and 24:00 will
    # NOT get you 24:00.  The only way to get 24:00 is to create
    # a 24:00 instance
    t = HHMMTime(0, 1) - 1
    assert t.hours == 0 and t.minutes == 0
    t -= 1
    assert t.hours == 23 and t.minutes == 59
    t += 1
    assert t.hours == 0 and t.minutes == 0

def test_representation():
    '''
    Test the string representations
    '''
    t = HHMMTime('11:45')
    assert str(t) == '11:45'
    assert repr(t) == "HHMMTime('11:45')"

def test_validation():
    '''
    Test that the input validations work
    '''
    with pytest.raises(ValueError) as e:
        t = HHMMTime('24.01')
    with pytest.raises(ValueError) as e:
        t = HHMMTime('24:01')
    with pytest.raises(ValueError) as e:
        t = HHMMTime(24, 1)
    with pytest.raises(ValueError) as e:
        t = HHMMTime(-1, 0)
