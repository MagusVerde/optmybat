#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Classes for reading and setting paramters.
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

from util.classydict import ClassyDict

class Register(object):
    '''
    Represents a Inverter register (parameter) including code to parse
    and generate objects for communicating with the inverter.
    '''
    def __init__(self, name):
        '''
        :param name: the register's simple name - must be unique and
                     usable as a Python variable name
        '''
        self.name = name
        self.initialised = False

    def parse(self, props):
        '''
        Configure myself from a properties dict returned by the inverter.
        '''
        if not isinstance(props, ClassyDict):
            props = ClassyDict(props)
        self.id = props.param_id
        self.addr = props.param_addr
        self.type = props.param_type
        self.pname = props.param_name
        self.value = props.param_value
        self.initialised = True
        return self

    def dump(self):
        '''
        :returns: a dict() suitable for passing to the inverter
        '''
        if self.initialised:
            return {
                'param_id': self.id,
                'param_addr': self.addr,
                'param_type': self.type,
                'param_name': self.pname,
                'param_value': self.value
            }
        else:
            # Not yet initialized - return an empty dict
            return ClassyDict()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}') {self.dump()}"

    def __str__(self):
        properties = self.dump()
        properties['name'] = self.name
        return str(properties)

class Parameters(ClassyDict):
    '''
    Provides a way mapping registers to and from the inverter in bulk
    '''

    def __init__(self, params=None):
        '''
        :param params: a dict() mapping param_addresses to objects
        '''
        super().__init__()
        if params is not None:
            self._params = params
        else:
            self._params = dict()

    def loadAddressMap(self, param_map):
        '''
        Add the params map from a dict of names mapped to addresses.
        '''
        for (name, address) in param_map.items():
            self._params[address] = Register(name)
        return self

    def parse(self, plist):
        '''
        Configure myself from a list of registers provided by the inverter.

        :param plist: A list of register dicts() from the inverter
        '''
        for p in plist:
            addr = p['param_addr']
            if addr in self._params:
                param = self._params[addr]
                param.parse(p)
                self[param.name] = param
        return self

    def dump(self):
        '''
        Dump the list of registers suitable for passing to the inverter.
        '''
        return [v.dump() for (n, v) in self.items() if n != '_params']

    def __len__(self):
        '''
        Don't include the _params property in my length.
        '''
        return super().__len__() - 1
