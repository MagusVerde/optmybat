#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Ask the WiNet-S dongle to reboot.
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

import sys
import time

from sungrow.services import Services
from sungrow.support import SungrowError
from util.config import Config

def doWork():
    '''
    Wrap the real work in some exception handling
    '''
    did_it = False
    config = Config.load()
    # Force the timeout to be huge
    config.timeout = 60
    logger = config.logger
    try:
        client = Services()
        did_it = client.reboot()
        client.close()
    except SungrowError as err:
        logger.critical(err)
    except Exception as err:
        logger.critical('Unexpected %s exception', type(err).__name__, exc_info = True)
    return did_it

def main(args):
    did_it = False
    try:
        did_it = doWork()
    except KeyboardInterrupt:
        pass
    # Exit appropriately
    sys.exit(0 if did_it else 1)
