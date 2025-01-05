#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# Sungrow services.
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
import time

from sungrow.client import Client
from sungrow.parameters import Parameters
from sungrow.sh5params import SH5_FORCE_CHARGE_PARAM_MAP, SH5_FORCE_CHARGE_PARAMS, SH5_POWER_STATS_MAP, SH5_BATTERY_STATS_MAP
from sungrow.support import SungrowError
from util.classydict import ClassyDict
from util.config import Config
from util.hhmmtime import HHMMTime

#-----------------------------------------------------------------
# Some common, but not obvious, constants
SH5_ENABLE = 170
SH5_DISABLE = 85
SH5_WEEKDAY_ONLY = '0'
SH5_ALL_DAYS = '1'

class Services(object):
    '''
    A simple client for talking to a Sungrow inverter via a WiNet-S dongle.
    '''
    def __init__(self, host=None):
        '''
        Initiate myself then connect.
        '''
        # Load the configurations
        config = self.config = Config.load()
        # The inverter interface is slooow so we cache some responses for this many seconds
        self.cache_seconds = config.timeout * 2
        # Configure self.logger
        self.logger = config.logger
        # Make the connection
        self.client = Client(host=host)
        # Prepare the caches
        self.battery = ClassyDict({'service': 'real_battery', 'property_map': SH5_BATTERY_STATS_MAP, 'updated': 0})
        self.power = ClassyDict({'service': 'real', 'property_map': SH5_POWER_STATS_MAP, 'updated': 0})
        self.force_charge = ClassyDict({'updated': 0})

    def close(self):
        '''
        Good night sweet prince
        '''
        self.client.close()

    def getCachedParams(self, cache):
        '''
        Cache and return some information from the inverter
        '''
        # Use the cached info if it's less than a few seconds old
        now = time.time()
        if cache.updated >= now - self.cache_seconds:
            return cache
        # Refresh the cache
        values = self.client.call(service=cache.service, dev_id=self.client.inverter_id).list
        property_map = cache.property_map
        new = dict()
        for data in values:
            name = data['data_name']
            if name in property_map:
                new[property_map[name]] = data['data_value']
        # And set missing properties to '--'
        for p in property_map.values():
            if not p in new:
                new[p] = '--'
        cache.update(new)
        cache.updated = now
        self.logger.debug("cached %s details are %s", cache.service, cache)
        return cache

    def getInverterStats(self):
        '''
        Get an accumulated set of status information from the inverter
        '''
        stats = ClassyDict()
        stats.update(self.getCachedParams(self.power))
        stats.update(self.getCachedParams(self.battery))
        stats['force_charge_status'] = str(self.getForceChargeStatus())
        return stats

    @classmethod
    def getInverterStatNames(cls):
        '''
        Get an accumulated set of status information from the inverter
        '''
        names = list(SH5_BATTERY_STATS_MAP.values()) + list(SH5_POWER_STATS_MAP.values())
        names.append('force_charge_status')
        return sorted(names)

    def getBatteryCharging(self):
        '''
        Return the charge/discharge rate.  Positive number means it's
        charging, negative number means it's discharging.
        '''
        info = self.getInverterStats()
        if info.battery_charging_power == '--' or info.battery_discharging_power == '--':
            raise SungrowError(f"Current battery charge rate is undefined")
        return float(info.battery_charging_power) - float(info.battery_discharging_power)

    def getBatterySOC(self):
        '''
        Return the current battery State of Charge
        '''
        soc = self.getInverterStats().battery_level_soc
        if soc == '--':
            raise SungrowError(f"Current battery state of charge is undefined")
        self.logger.debug(f'Current SOC is {soc}%')
        return float(soc)

    def getForceChargeStatus(self):
        '''
        Returns the current force charge state - a number between 0 and 100.
        If 0, force charge is disabled.

        Note: assumes that force charging is applied every day
        '''
        # Use the cached info if it's less than a few seconds old
        now = time.time()
        fcp = self.force_charge
        if fcp.updated >= now - self.cache_seconds:
            return fcp.status
        # Read the force charg status from the inverter
        fcp = self.force_charge = Parameters().loadAddressMap(SH5_FORCE_CHARGE_PARAM_MAP)
        # Get the energy management parameters
        r = self.client.get('/device/getParam', params={'dev_id':self.client.inverter_id, 'dev_type':self.client.inverter_type, 'dev_code':{self.client.inverter_code},'type':9})
        # Update our internal state
        if not 'list' in r:
            raise SungrowError("Unexpected getParam response - {r}")
        fcp.parse(r.list)
        if not 'fc_enable' in fcp:
            raise SungrowError("Unexpected getParam response - {r}")
        # Update the cache timestamp
        fcp.updated = now
        fcp.status = 0.0  # assume it's disabled
        # Is it even enabled
        if int(fcp.fc_enable.value) != SH5_ENABLE:
            # Force charging is not enabled
            self.logger.debug("Force charge is not enabled")
            return fcp.status
        # target soc of 0 means force charging is disabled
        if int(fcp.fc1_soc.value) == 0 and int(fcp.fc2_soc.value) == 0:
            # Targets are 0
            self.logger.debug("Force charge is set to 0% at the inverter")
            return fcp.status
        # Get the time difference between this machine and the inverter
        timeslip = self.getInverterTimeShift()
        # For convenience, get easier to handle start and end times
        fc1_start = HHMMTime(fcp.fc1_start_hr.value, fcp.fc1_start_min.value)
        fc1_end = HHMMTime(fcp.fc1_end_hr.value, fcp.fc1_end_min.value)
        fc2_start = HHMMTime(fcp.fc2_start_hr.value, fcp.fc2_start_min.value)
        fc2_end = HHMMTime(fcp.fc2_end_hr.value, fcp.fc2_end_min.value)
        # Check start and end times
        now = HHMMTime.now() + timeslip
        self.logger.debug(f"Checking {fc1_start}-{fc1_end} and {fc2_start}-{fc2_end} against {now}")
        if now >= fc1_start and now <= fc1_end:
            # In the the first time range
            fcp.status = float(fcp.fc1_soc.value)
        elif now >= fc2_start and now <= fc2_end:
            # In the the second time range
            fcp.status = float(fcp.fc2_soc.value)
        return fcp.status

    def getInverterTimeShift(self):
        '''
        Gets the difference in minutes between time on the inverter and local time.
        Primarily designed to handle daylight saving shifts but can also handle the
        case where the inverter's time is simply wrong.

        :returns: the difference (in minutes) between the time on the inverter
                and local time - needed to accurately set times on the inverter.
        '''
        # Only request it if we don't already have it
        if not hasattr(self, 'sg_timeslip'):
            # Request the time from the inverter
            r = self.client.get('/time/get')
            # Convert it to an epoch time
            now = datetime.now(tz=self.config.timezone)
            inverter_now = datetime.strptime(r.time, '%Y-%m-%d %H:%M')
            if self.config.timezone is not None:
                inverter_now = self.config.timezone.localize(inverter_now)
            self.sg_timeslip = int((inverter_now - now).total_seconds() / 60)
            if abs(self.sg_timeslip) > 60:
                self.logger.warning(f"Inverter time ({r.time}) is radically different to local time")
                self.sg_timeslip %= HHMMTime.ONE_DAY
            elif abs(self.sg_timeslip) == 1:
                # Don't care about one minute difference
                self.sg_timeslip = 0
            self.logger.debug('Time difference is %d minutes', self.sg_timeslip)
        return self.sg_timeslip

    def getStatus(self):
        '''
        Return status indicators.
        '''
        power = self.getInverterStats()
        # ClassyDict for the results
        stats = ClassyDict()
        stats.soc = self.getBatterySOC()
        stats.fc_state = self.getForceChargeStatus()
        stats.battery = self.getBatteryCharging()
        stats.mains = float(power.purchased_power)
        stats.raw = power
        return stats

    def reset(self):
        '''
        Reset to known good state
        '''
        # Set the "safe" parameters
        safe = Parameters()
        safe.loadRegisters(SH5_FORCE_CHARGE_PARAMS)
        safe.em_mode.value = '0'    # Self consumption mode
        safe.fc_enable.value = SH5_DISABLE   # Force charge disabled
        return self.client.setParams(safe)

    def setForceCharge(self, target):
        '''
        :param target: an TimedTarget specifying the start and end times and
                    the target battery level
        '''
        # Load the status
        self.getForceChargeStatus()
        fcp = self.force_charge
        # Make sure we have the parameters
        if not 'fc1_start_hr' in fcp:
            # Must be enabled to get all of the params
            fcp.fc_enable.value = SH5_ENABLE
            self.client.setParams(fcp)
            # Then do another call to get the values
            self.getForceChargeStatus()
            if not 'fc1_start_hr' in fcp:
                raise SungrowError(f'Eh? Not getting the parameters from the inverter')
        # Convenience variables
        fc1_soc = target.target
        fc2_soc = 0     # Assume we won't need the second time slot
        # Get the inverter time shift and calculate the real start
        # and end times accounting for time wrapping
        if fc1_soc == 0:
            # Target is 0 - force disable
            fc1_start = fc1_end = HHMMTime('00:00')
        else:
            timeslip = self.getInverterTimeShift()
            fc1_start = target.start + timeslip
            fc1_end = target.stop + timeslip
            if fc1_start > fc1_end:
                # time wrap!
                fc2_start = HHMMTime('00:00')
                fc2_end = fc1_end
                fc2_soc = fc1_soc
                fc1_end = HHMMTime('24:00')
        if fc2_soc == 0:
            # Don't need the second time slot
            fc2_start = fc2_end = HHMMTime('00:00')
        # Update the force charge parameters for the new settings
        fcp.fc_enable.value = SH5_ENABLE
        fcp.fc_weekdays_only.value = SH5_ALL_DAYS
        fcp.fc1_start_hr.value = fc1_start.hours
        fcp.fc1_start_min.value = fc1_start.minutes
        fcp.fc1_end_hr.value = fc1_end.hours
        fcp.fc1_end_min.value = fc1_end.minutes
        fcp.fc1_soc.value = fc1_soc
        fcp.fc2_start_hr.value = fc2_start.hours
        fcp.fc2_start_min.value = fc2_start.minutes
        fcp.fc2_end_hr.value = fc2_end.hours
        fcp.fc2_end_min.value = fc2_end.minutes
        fcp.fc2_soc.value = fc2_soc
        # Apply the new settings
        if not self.client.setParams(fcp):
            raise SungrowError(f"Failed to set forced charge to minimum {target}")
        # Make sure that the parameters are read again next time
        fcp.updated = 0
        self.logger.debug(f"Set force charge to minimum {target}")
