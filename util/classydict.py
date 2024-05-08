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

class ClassyDict(dict):
    '''
    A dict wrapper that allows the elements of the dictionary to be accessed
    as if they were object properties (e.g. you can use both d.var and d['var']).
    This looks nicer if you're dealing with a dict that has a known, regular
    structure where the keys are strings that can be used as Python variable names.

    Not recommended for dicts where the keys are not mappable to a varable
    name.  The class will work correctly with keys like True, int(1), 'a-b',
    [1, 2, 3] but, of course, you can't access those elements as variables.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __delattr__(self, name):
        '''
        Delete the item from my data
        '''
        super().__delitem__(name)

    def __getattr__(self, name):
        '''
        Return a field element as if it was an attribute.
        '''
        if not super().__contains__(name):
            raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        '''
        Allow for updating the UserDict properties
        '''
        self.__setitem__(name, value)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"
