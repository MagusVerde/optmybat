#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Wrapper supporting configurable monitoring options.
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

import importlib

from util.config import Config

class Monitoring(object):
    '''
    Process the configuration information and enable all configured monitoring stores
    '''
    def __init__(self, stores, fields):
        '''
        Initiate myself.

        param: stores - list of monitoring store names and associated properties
        param: properties - the list of fields to be saved
        '''
        # Save the list of properties
        self.properties = fields
        # Create list of the configured monitoring stores
        self.stores = list()
        for store in stores:
            m = importlib.import_module(f'monitoring.{store['engine']}')
            self.stores.append(m.Persist(store, fields))

    def save(self, status):
        '''
        Save the passed status to all configured monitoring stores
        '''
        for s in self.stores:
            s.save(status)

