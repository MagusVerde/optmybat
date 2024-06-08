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
from sungrow.sh5params import SH5_FORCE_CHARGE_PARAM_MAP, SH5_BATTERY_PROPERTY_MAP, SH5_FORCE_CHARGE_PARAMS, SH5_REALTIME_POWER_MAP
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
    def __init__(self, host=None, port=None):
        '''
        Initiate myself then connect.
        '''
        # Load the configurations
        config = self.config = Config.load()
        # Configure self.logger
        self.logger = config.logger
        # Make the connection
        self.client = Client(host=host, port=port)
        # Prepare the battery info cache
        self.battery = ClassyDict({'updated': 0})

    def close(self):
        '''
        Good night sweet prince
        '''
        self.client.close()

    def getBatteryInfo(self):
        '''
        Get selected info about the battery's current state
        '''
        # Use the cached info if it's less than a few seconds old
        now = time.time()
        if self.battery.updated >= now - 3:
            return self.battery
        # Map Sungrow property names to battery properties
        property_map = SH5_BATTERY_PROPERTY_MAP
        values = self.client.call(service='real_battery', dev_id=self.client.inverter_id).list
        battery = ClassyDict({"updated": now})
        for data in values:
            name = data.get('data_name', None)
            if name in property_map:
                battery[property_map[name]] = data['data_value']
        # And set missing propreties to '--'
        for p in property_map.values():
            if not p in battery:
                battery[p] = '--'
        self.battery = battery
        self.logger.debug("battery details are %s", battery)
        return battery

    def getBatteryCharging(self):
        '''
        Return the charge/discharge rate.  Positive number means it's
        charging, negative number means it's discharging.
        '''
        info = self.getBatteryInfo()
        if info.charge_kw == '--' or info.discharge_kw == '--':
            raise SungrowError(f"Current battery charge rate is undefined")
        return float(info.charge_kw) - float(info.discharge_kw)

    def getBatterySOC(self):
        '''
        Return the current battery State of Charge
        '''
        soc = self.getBatteryInfo().soc
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
        # use the already gotten value
        if not hasattr(self, 'forceChargeParams'):
            self.forceChargeParams = Parameters().loadAddressMap(SH5_FORCE_CHARGE_PARAM_MAP)
        fcp = self.forceChargeParams
        # Get the energy management parameters
        r = self.client.get('/device/getParam', params={'dev_id':self.client.inverter_id, 'dev_type':self.client.inverter_type, 'dev_code':{self.client.inverter_code},'type':9})
        # Update our internal state
        if not 'list' in r:
            raise SungrowError("Unexpected getParam response - {r}")
        fcp.parse(r.list)
        if not 'fc_enable' in fcp:
            raise SungrowError("Unexpected getParam response - {r}")
        # Is it even enabled
        if int(fcp.fc_enable.value) != SH5_ENABLE:
            # Force charging is not enableed
            return 0.0
        # target soc of 0 means force charging is disabled
        if int(fcp.fc1_soc.value) == 0 and int(fcp.fc2_soc.value) == 0:
            # Targets are 0
            self.logger.debug("Force charge is set to 0% at the inverter")
            return 0.0
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
            return float(fcp.fc1_soc.value)
        if now >= fc2_start and now <= fc2_end:
            # In the the second time range
            return float(fcp.fc2_soc.value)
        return 0.0

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

    def getPowerStats(self):
        # Map Sungrow property names to power stats
        power_map = SH5_REALTIME_POWER_MAP
        values = self.client.call(service='real', dev_id=self.client.inverter_id).list
        stats = ClassyDict()
        for data in values:
            name = data.get('data_name', None)
            if name in power_map:
                stats[power_map[name]] = data['data_value']
        return stats

    def getStatus(self):
        '''
        Return status indicators.
        '''
        power = self.getPowerStats()
        # ClassyDict for the results
        stats = ClassyDict()
        stats.soc = self.getBatterySOC()
        stats.fc_state = self.getForceChargeStatus()
        stats.battery = self.getBatteryCharging()
        stats.mains = float(power.purchased_power) - float(power.feed_power)
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
        # Need to have already loaded the params to be able to set them
        if not hasattr(self, 'forceChargeParams'):
            self.getForceChargeStatus()
        fcp = self.forceChargeParams
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
        self.logger.debug(f"Set force charge to minimum {target}")
        