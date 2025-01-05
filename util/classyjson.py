#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# A ClassyDict variant that supports direct translation to/from JSON
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
from util.classydict import ClassyDict

class ClassyJSON(ClassyDict):
    '''
    A JSON compatible variation on ClassyDict
    '''

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str):
            self.load(args[0])
            args = ()
        super().__init__(*args, **kwargs)

    def load(self, json_str):
        '''
        Load myself from a json string
        '''
        for n, v in json.loads(json_str).items():
            self[n] = v

    def dump(self):
        '''
        Convert myself in to a JSON string
        '''
        return json.dumps(self)

    def __str__(self):
        return self.dump()
