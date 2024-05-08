#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# The main runtime entry point for Optmybat.
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

from sungrow.client import Client, SungrowError
from sungrow.support import TimedTarget
from util.config import Config
from util.hhmmtime import HHMMTime

def updateForceCharge(config):
    '''
    Check the targets against the current force charge state and,
    if needed, update the force charge state.
    '''
    # Get connected and authenticate as a power user
    logger = config.logger
    client = Client()
    client.authenticate(config.admin_user, config.admin_passwd)
    # Get the current inverter and battery state
    soc = client.getBatterySOC()
    fc_target = client.getForceChargeStatus()
    # Search for a target that is active now AND the battery level is lower
    # than the target.  If none, the target will be to disable force charging
    timings = TimedTarget.loadTargets(config.soc_min)
    logger.debug("Targets are %s", timings)
    target = None
    now = HHMMTime.now()
    for t in timings:
        if now >= t.start and now < t.stop and soc <= t.target:
            target = t
            break
    logger.debug(f"SoC is {soc}%, Force Charge is {'disabled' if fc_target == 0 else fc_target}, want {target}")
    # Work out what needs to be done
    if target is None:
        # Either there is no target at this time or the current
        # battery level is higher than the required target so
        # we need to ensure force charging is disabled
        if fc_target != 0:
            # Force charging is on - turn it off
            target = TimedTarget('00:00', '00:00', 0)
    elif fc_target == target.target:
        # the battery is less than or equal to target but
        # force charging is already correctly set - do nothing
        target = None
    else:
        # Need to update force charging
        target.start = now - 1
    # Do the needful
    if target is None:
        logger.info(f"Doing nothing - battery is {soc}%")
    else:
        if target.target == 0:
            logger.info('Disabling force charge')
        else:
            logger.info(f"Setting force charge to {target.target}% until {target.stop}")
        client.setForceCharge(target)
    client.close()
    return target is not None

def doWork():
    '''
    Wrap the real work in some exception handling
    '''
    did_it = False
    config = Config.load()
    logger = config.logger
    try:
        did_it = updateForceCharge(config)
    except SungrowError as err:
        logger.critical(err)
    except Exception as err:
        logger.critical('Unexpected %s exception' % type(err).__name__, exc_info = True)
    return did_it

def main(args):
    try:
        if args.once:
            did_it = doWork()
        else:
            did_it = True
            while True:
                if not doWork():
                    did_it = False
                time.sleep(Config.load().poll_interval)
    except KeyboardInterrupt:
        pass
    # Exit appropriately
    sys.exit(0 if did_it else 1)
