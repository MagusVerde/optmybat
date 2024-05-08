#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# A client for Sungrow Hybrid Inverters.
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
import json
from websocket import create_connection, WebSocketTimeoutException
import requests

from sungrow.parameters import Parameters
from sungrow.sh5params import SH5_FORCE_CHARGE_PARAM_MAP
from sungrow.support import TimedTarget
from util.classydict import ClassyDict
from util.config import Config
from util.hhmmtime import HHMMTime

#-----------------------------------------------------------------
# Some common, but not obvious, constants
SH5_ENABLE = 170
SH5_DISABLE = 85
SH5_WEEKDAY_ONLY = '0'
SH5_ALL_DAYS = '1'

#-----------------------------------------------------------------
# The exception we raise
class SungrowError(Exception):
    '''
    A class specific exception
    '''
    def __init__(self, msg):
        super().__init__(msg)

class Client(object):
    '''
    A simple client for talking to a Sungrow inverter via a WiNet-S dongle.
    '''
    def __init__(self, host=None, port=None):
        '''
        Get some configuration and initiate a connection.
        '''
        # Load the configurations
        config = self.config = Config.load()
        # Configure self.logger
        self.logger = config.logger
        # Configure the websocket connection basics
        if host is None:
            host = config.sg_host
        if port is None:
            port = config.sg_ws_port
        self.sg_host = host
        self.sg_ws_port = port
        self.timeout = config.timeout
        self.ws_endpoint = f'ws://{self.sg_host}:{self.sg_ws_port}/ws/home/overview'
        # Try to establish a connection immediately
        self.ws_socket = None
        self.ws_token = ''
        if not self.connect():
            raise SungrowError(f"Can't connect to {self.sg_host}:{self.sg_ws_port}")
        self.logger.debug('Connected to %s:%d', self.sg_host, self.sg_ws_port)

    # Basic methods
    def connect(self):
        '''
        Connect via WebSocket to the dongle and fetch some information.

        :returns: True if connection succeeded, False otherwise
        '''
        # If already connected, close it.
        if self.ws_token != '':
            self.close()
        # Try to open the connection
        try:
            self.ws_socket = create_connection(self.ws_endpoint, timeout=self.timeout)
        except Exception as err:
            self.logger.debug('Websocket connection to %s failed - %s', self.ws_endpoint, err)
            return False
        self.logger.debug('Connected to %s', self.ws_endpoint)
        # Get a new token
        result = self.call(service='connect')
        self.ws_token = result.token
        # Get some basic information
        self.logger.debug('Requesting Device Information')
        result = self.call(service='devicelist', type='0', is_check_token='0')
        # Check that this is what we're expecting and set the device details
        self.dev_id = None
        for d in result.list:
            if d['dev_type'] == 35:
                # Gotcha
                self.dev_id = str(d['dev_id'])
                self.dev_code = str(d['dev_code'])
                self.dev_model = d['dev_model']
                self.dev_type = str(d['dev_type'])
        if self.dev_id is None:
            raise SungrowError(f'{self.sg_host} ({result.list[0]['dev_model']}) is not a hybrid inverter')
        return True

    def close(self):
        '''
        Properly close the websocket.

        :returns: True if the socket was open.
        '''
        if self.ws_socket is not None:
            self.ws_socket.close()
            self.ws_socket = None
            self.ws_token = ''
            self.logger.debug('Closed websocket connection to %s:%s', {self.sg_host}, {self.sg_ws_port})
            return True
        return False

    def call(self, **kwargs):
        '''
        Make a websocket call.  Automatically adds the token.

        :param kwargs: the arguments to the websocket call
        :returns: a ClassyDict containing the result_data.
        :raises: SungrowError if there was a problem.
        '''
        if 'service' not in kwargs or kwargs['service'] is None:
            raise SungrowError('The websocket call requires a service name')
        if 'lang' not in kwargs:
            kwargs['lang'] = 'en_us'
        kwargs['token'] = self.ws_token
        try:
            self.logger.debug('Calling %s', json.dumps(kwargs))
            self.ws_socket.send(json.dumps(kwargs))
            r = self.ws_socket.recv()
        except WebSocketTimeoutException:
            raise SungrowError(f"Timeout calling {kwargs['service']}")
        # Convert the reponse
        rdata = self._parse_response(r)
        return rdata

    def get(self, uri, **kwargs):
        '''
        GET something from the inverter. Automatically adds the token to the request.

        :param uri: Request uri (minus host and protocol)
        :param kwargs: additional requests.get argument
        :returns: a ClassyDict containing the result_data.
        :raises: SungrowError if there was a problem.
        '''
        # Make sure there is a params argument
        if 'params' not in kwargs:
            kwargs['params'] = dict()
        # And a timeout arg
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        # Add the token to the params
        kwargs['params']['token'] = self.ws_token
        self.logger.debug('GET http://%s%s', self.sg_host, uri)
        try:
            r = requests.get(f'http://{self.sg_host}{uri}', **kwargs)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            raise SungrowError(f"Time out while trying to access http://{self.sg_host}{uri}")
        if r.status_code != 200:
            raise SungrowError(f'Failed to access http://{self.sg_host}{uri} - {r.status_code} - {r.text}')
        # Convert the reponse
        rdata = self._parse_response(r.text)
        return rdata

    # Higher order utilitites
    def authenticate(self, username, password):
        '''
        Login to the inverter.
        '''
        result = self.call(service='login',passwd=password, username=username)
        self.ws_token = result.token

    def getBatterySOC(self):
        '''
        Return the current battery State of Charge
        '''
        result = self.call(service='real_battery', dev_id=self.dev_id)
        soc = '--'
        for data in result.list:
            if 'data_name' in data and data['data_name'] == 'I18N_COMMON_BATTERY_SOC':
                soc = data['data_value']
                break
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
        r = self.get('/device/getParam', params={'dev_id':self.dev_id, 'dev_type':self.dev_type, 'dev_code':{self.dev_code},'type':9})
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
            r = self.get('/time/get')
            # Convert it to an epoch time
            now = datetime.now(tz=self.config.timezone)
            inverter_now = datetime.strptime(r.time, '%Y-%m-%d %H:%M')
            if self.config.timezone is not None:
                inverter_now = self.config.timezone.localize(inverter_now)
            print(f"inverter_now = {inverter_now}")
            self.sg_timeslip = int((inverter_now - now).total_seconds() / 60)
            if abs(self.sg_timeslip) > 60:
                self.logger.warning(f"Inverter time ({r.time}) is radically different to local time")
                self.sg_timeslip %= HHMMTime.ONE_DAY
            elif abs(self.sg_timeslip) == 1:
                # Don't care about one minute difference
                self.sg_timeslip = 0
            self.logger.debug('Time difference is %d minutes', self.sg_timeslip)
        return self.sg_timeslip

    def setParams(self, params):
        '''
        Set some parameter values on the inverter

        :param params: A Parameters object containing the registers that need to be set

        :returns: True if the setting worked
        '''
        result = self.call(
            service='param',
            dev_code=self.dev_code,
            dev_type=self.dev_type,
            devid_array=[self.dev_id],
            type='9',
            count='1',
            list=params.dump()
        )
        # Check for success
        for r in result.list:
            if 'param_pid' not in r:
                self.logger.warning(f"Eh? Unexpected result from parameter setting - {result}")
            elif r['param_pid'] != -1 and r['result'] != 0:
                self.logger.debug(f"Failed to set {r}")
                return False
        return True

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
            self.setParams(fcp)
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
        if not self.setParams(fcp):
            raise SungrowError(f"Failed to set forced charge to minimum {target}")
        self.logger.debug(f"Set force charge to minimum {target}")

    # Utility methods
    def _parse_response(self, body):
        '''
        Parse the response from a request to the inverter.  Raises an
        SungrowError if not the expected format or the response contains
        an error.  Otherwise it returns a ClassyDict of the result_data.
        '''
        try:
            r = json.loads(body)
        except json.decoder.JSONDecodeError:
            raise SungrowError(f'Non-JSON response - {r.text}')
        if 'result_code' not in r or 'result_msg' not in r or 'result_data' not in r:
            raise SungrowError(f'Unexpected response - {r}')
        if r['result_code'] != 1:
            raise SungrowError(f'Received error response code {r['result_code']} - {r['result_msg']}')
        return ClassyDict(r['result_data'])
