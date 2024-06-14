#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Persist status information to a CSV
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
import os

from util.config import Config

class Persist(object):
    '''
    Save status information
    '''
    def __init__(self, parameters, column_list):
        '''
        Initiate myself.

        param: parameters - configuration parameters for this monitoring engine
        param: field_list - the list of fields to be saved
        '''
        # Load the configurations
        config = self.config = Config.load()
        # Configure self.logger
        self.logger = config.logger
        # Set my paramters
        self.dest = parameters['dest']
        self.columns = column_list

    def save(self, status):
        '''
        Save a row of data
        '''
        now = datetime.now(tz=self.config.timezone).strftime('%Y-%m-%d %H:%M:%S')
        # If the file doesn't exist, create it and write the header
        exists = os.path.exists(self.dest)
        # Open the file
        with open(self.dest, "a") as ofd:
            if not exists:
                ofd.write("timestamp,")
                ofd.write(self.dumpline(self.columns))
            cells = list()   
            for c in self.columns:
                cells.append(status[c])
            ofd.write(f"{now},")
            ofd.write(self.dumpline(cells))

    def dumpline(self, cells):        
        '''
        Return a line of comma separated cells
        '''
        line = ''
        for c in cells:
            if ',' in c:
                c = f'"{c}"'
            line = line + c + ','
        return line[:-1] + '\n'
