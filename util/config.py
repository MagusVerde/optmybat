#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# A support module for Optmybat that encapsulates all configuration parameters.
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

import logging
import os
import pytz
import yaml

from util.classydict import ClassyDict

class Config(ClassyDict):
    '''
    Wrapper class for all configuration parameters.  While this is a ClassyDict and
    therefore writable, it is implemented as a singleton so there is a single, read
    only instance shared across all callers.
    '''

    # The default configuration values
    _DEFAULTS = {
        'sg_host': 'inverter',
        'sg_ws_port': 8082,
        'admin_user': 'user',
        'admin_passwd': 'pw1111',
        'timeout': 4,
        'log_level': 'INFO',
        'poll_interval': 30,
        'soc_min': [ ],
        'soc_max': [ ],
        'timezone': None
    }

    def __init__(self):
        '''
        Throw an exception if _instance class variable doesn't exist, otherwise
        create it and set it to myself.
        '''
        clz = self.__class__
        if not hasattr(clz, '_instance'):
            raise Exception('Invalid call to Config() - use Config.load() instead')
        clz._instance = self
        # Find the config file
        if 'SH5_CONFIG' in os.environ:
            self.config_path = os.environ['SH5_CONFIG']
        elif os.path.exists(f"{os.environ["HOME"]}/.optmybat.config"):
            self.config_path = f"{os.environ["HOME"]}/.optmybat.config"
        else:
            self.config_path = 'config/config.yml'
        self.config_mtime = 0
        # Init myself from the default values
        super().__init__(Config._DEFAULTS)

    @classmethod
    def unload(clz):
        '''
        Destroys the existing singleton so it can be created anew.
        Primarily used for testing.
        '''
        if hasattr(clz, '_instance'):
            delattr(clz, '_instance')

    @classmethod
    def load(clz):
        '''
        Returns a "new" instance of the configuration which is really a singleton shared
        across all instances.
        '''
        if not hasattr(clz, '_instance') or clz._instance._hasConfigChanged():
            clz._instance = None
            config = Config()
            # Merge in whatever was read from the config file
            for (name, value) in config._readConfig().items():
                config[name] = value
            # Set the logging level
            config._init_logger()
            # Set the time zone
            if not config.timezone:
                config.timezone = None
            else:
                config.timezone = pytz.timezone(config.timezone)
        else:
            config = clz._instance
        return config

    def _init_logger(self):
        logging.basicConfig(
            format='%(asctime)s: %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger()
        self.logger.setLevel(self.log_level)

    def _hasConfigChanged(self):
        '''
        Finds the config file and checks if it's modified time
        has changed.

        :returns: True if the file has changed
        '''
        return self.config_path != '' and (self.config_mtime == 0 or self.config_mtime < os.stat(self.config_path).st_mtime)

    def _readConfig(self):
        '''
        Find and read the config file.
        '''
        # An empty SH5_CONFIG means only use defaults - useful for testing
        if self.config_path == '':
            return dict()
        # Otherwise, use the specified file
        self.config_mtime = os.stat(self.config_path).st_mtime
        with open(self.config_path, 'r', encoding='utf-8') as fd:
            return yaml.safe_load(fd)
