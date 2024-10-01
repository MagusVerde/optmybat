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

    ClassyDict handles "hidden" variables (those starting with an '_'), hiding them
    from the 'in' operator and the keys(), items(), len(), repr() and str()
    methods.  This means that they can only be seen and accessed by direct
    reference - either ClassyDict()['_name'] or ClassyDict()._name.  To see what
    happens with private items, have a look at test_ClassyDict.testPrivateAttribues().
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all private items into private attributes
        for k in list(super().keys()):
            if k[0] == '_':
                v = super().__getitem__(k)
                super().__delitem__(k)
                super().__setattr__(k, v)

    def __delattr__(self, name):
        '''
        Delete the item from my data
        '''
        if name[0] == '_':
            super().__delattr__(name)
        else:
            super().__delitem__(name)

    def __getattr__(self, name):
        '''
        Return a field element as if it was an attribute.
        '''
        try:
            if name[0] == '_':
                return super().__getattribute__(name)
            else:
                return super().__getitem__(name)
        except KeyError:
            raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")

    def __setattr__(self, name, value):
        '''
        Update/add a field to the underlying dict
        '''
        if name[0] == '_':
            super().__setattr__(name, value)
        else:
            super().__setitem__(name, value)

    def __delitem__(self, name):
        try:
            return self.__delattr__(name)
        except AttributeError:
            raise KeyError(name)

    def __getitem__(self, name):
        try:
            return self.__getattr__(name)
        except AttributeError:
            raise KeyError(name)

    def __setitem__(self, name, value):
        return self.__setattr__(name, value)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self):
        return super().__repr__()