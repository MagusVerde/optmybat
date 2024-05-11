#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# A class that handles time expressed as hours and minutes.  Supports full
# modulo artihmetic and arithmetic comparison.
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

class HHMMTime(object):
    '''
    The maximum value of an HHMMTime.
    '''
    ONE_DAY = 24 * 60

    # Helper methods
    @classmethod
    def __parse(cls, hhmmstr):
        '''
        Convert a string of the format hh:mm to an integer tuple
        '''
        try:
            (hh, mm) = hhmmstr.split(':')
            hh = int(hh)
            mm = int(mm)
            return (hh, mm)
        except:
            raise ValueError(f"New HHMMTimes must of the format 'hh:mm' not '{hhmmstr}'")

    @classmethod
    def __wrap(cls, value):
        '''
        Modulo an arbitrary number to a valid HHMMTime range
        '''
        if abs(value) > HHMMTime.ONE_DAY:
            value = int(value) % HHMMTime.ONE_DAY
        if value < 0:
            value += HHMMTime.ONE_DAY
        return value

    @classmethod
    def now(cls):
        '''
        :returns: an HHMMTime representing the current minute
        '''
        t = datetime.now(tz=Config.load().timezone).timetuple()
        return HHMMTime(t.tm_hour, t.tm_min)

    def __init__(self, value, minutes=None):
        '''
        Create a new HHMMTime given either a string of the format hh:mm
        or a number.  Raises a ValueError if the string is badly formatted
        or out of range.
        '''
        if minutes is not None:
            hh = int(value)
            mm = int(minutes)
        elif isinstance(value, str):
            (hh, mm) = HHMMTime.__parse(value)
        elif isinstance(value, HHMMTime):
            hh = value.hours
            mm = value.minutes
        else:
            # Make sure value is an in-range integer
            value = self.__wrap(value)
            # Extract the hours and minutes
            (hh, mm) = divmod(value, 60)
        if hh < 0 or hh > 24 or (hh == 24 and mm > 0) or mm < 0 or mm > 59:
            raise ValueError(f"HHMMTimes must be between 00:00 and 24:00 not '{hh:02d}:{mm:02d}")
        self.hours = hh
        self.minutes = mm
        self.value = hh*60 + mm

    # Allow for addition and subtraction.  Note HHMMTimes wrap around the clock
    # for addition and subtraction.
    def __add__(self, other):
        if not isinstance(other, HHMMTime):
            other = HHMMTime(other)
        result = self.value + other.value
        if result == HHMMTime.ONE_DAY:
            result = 0
        return HHMMTime(HHMMTime.__wrap(result))

    def __sub__(self, other):
        if not isinstance(other, HHMMTime):
            other = HHMMTime(other)
        result = self.value - other.value
        if result == HHMMTime.ONE_DAY:
            result = 0
        return HHMMTime(HHMMTime.__wrap(result))

    # And for comparison and equivalence
    def __eq__(self, other):
        # Note that 24:00 == 00:00 so we need to explicitly handle that
        assert isinstance(other, HHMMTime)
        sv = 0 if self.value == HHMMTime.ONE_DAY else self.value 
        ov = 0 if other.value == HHMMTime.ONE_DAY else other.value 
        return sv == ov

    def __lt__(self, other):
        assert isinstance(other, HHMMTime)
        return self.value < other.value

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        assert isinstance(other, HHMMTime)
        return self.value > other.value

    def __ge__(self, other):
        return self > other or self == other

    # and string repre4sentations
    def __repr__(self):
        return f"HHMMTime('{self.hours:02d}:{self.minutes:02d}')"

    def __str__(self):
        return f'{self.hours:02d}:{self.minutes:02d}'
