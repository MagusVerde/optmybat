#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Support constants and classes for working with the WiNet-S Web Client.
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
from util.hhmmtime import HHMMTime

#-----------------------------------------------------------------
# Support classes
class SungrowTimer(object):
    '''
    Timers on the inverters are a block of 4 numbers: start_hr,
    start_min, stop_hr, stop_min.
    '''
    def __init__(self, start, stop):
        self.start = HHMMTime(start)
        self.stop = HHMMTime(stop)

    # Comparison and equivalence
    def __eq__(self, other):
        assert isinstance(other, SungrowTimer)
        return self.start == other.start and self.stop == other.stop

    def __lt__(self, other):
        assert isinstance(other, SungrowTimer)
        return self.start < other.start or (self.start == other.start and self.stop < other.stop)

    def __le__(self, other):
        assert isinstance(other, SungrowTimer)
        return self == other or self < other

    def __gt__(self, other):
        assert isinstance(other, SungrowTimer)
        return not other < self

    def __ge__(self, other):
        assert isinstance(other, SungrowTimer)
        return not other <= self

    # and string representations
    def __repr__(self):
        return f"SungrowTimer('{self.start}', '{self.stop}')"

    def __str__(self):
        return f"from {self.start} to {self.stop}"

class TimedTarget(SungrowTimer):
    '''
    Represents a timed target (e.g. Forced Chargeharge)
    '''
    def __init__(self, start, stop, target):
        super().__init__(start, stop)
        self.target = target

    def __repr__(self):
        return f"TimedTarget('{self.start}', '{self.stop}', {self.target})"

    def __str__(self):
        return f"target {self.target} from {self.start} to {self.stop}"

    @classmethod
    def loadTargets(cls, conf):
        '''
        Convert a list of text based target maps into a clean, ordered list
        of TimedTargets including resolving overlaps.
        '''
        # Step 1 - get the configured list converted to HHMMTimes
        targets = []
        for t in conf:
            if 'days' in t:
                # only applies on certain days
                dow = datetime.today().weekday()
                if dow not in t['days']:
                    continue
            if t['start'] == '24:00':
                t['start'] = '00:00'
            start = HHMMTime(t['start'])
            stop = HHMMTime(t['stop'])
            soc = int(t['target'])
            # Check for and handle wrapped times
            if start > stop:
                targets.append(TimedTarget(start, '24:00', soc))
                targets.append(TimedTarget('00:00', stop, soc))
            else:
                targets.append(TimedTarget(start, stop, soc))
        # Step 2 - Resolve any overlaps
        targets.sort()
        index = 1
        while index < len(targets):
            t1 = targets[index-1]
            t2 = targets[index]
            if t1 == t2:
                # Both entries have exactly the same start and stop times
                # Delete which ever has the smaller target
                if t1.target > t2.target:
                    del(targets[index])
                else:
                    del(targets[index-1])
            elif t1.stop > t2.start:
                # We have an overlap
                if t1.target == t2.target:
                    # simply merge the two
                    if t1.stop < t2.stop:
                        t1.stop = t2.stop
                    del(targets[index])
                elif t1.target < t2.target:
                    # Need to override t1 at this point
                    if t1.start == t2.start:
                        # t1 must be less than or equal to t2 so delete it
                        del(targets[index-1])
                    elif t1.stop <= t2.stop:
                        # truncate t1
                        t1.stop = t2.start
                        index += 1
                    else:
                        # Need to split t1 around t2
                        targets.append(TimedTarget(t2.stop, t1.stop, t1.target))
                        t1.stop = t2.start
                        targets.sort()
                        index = 1   # Need to start again because of the new times
                else:
                    # Need to override t2
                    if t2.stop < t1.stop:
                        # delete t2
                        del(targets[index])
                    else:
                        # truncate t2
                        t2.start = t1.stop
                        index += 1
            else:
                index += 1
        return targets
