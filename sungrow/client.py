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
import ssl
import requests
import urllib3
import websocket

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

class Client(object):
    '''
    A simple client for talking to a Sungrow inverter via a WiNet-S dongle.
    '''
    def __init__(self, host=None):
        '''
        Initiate myself then connect.
        '''
        # Suppress the insecure request warning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # Load the configurations
        config = self.config = Config.load()
        # Configure self.logger
        self.logger = config.logger
        # Configure the websocket connection basics
        if host is None:
            host = config.sg_host
        self.sg_host = host
        self.timeout = config.timeout
        self.ws_endpoint = f'wss://{self.sg_host}/ws/home/overview'
        # Try to establish a connection immediately
        self.ws_socket = None
        self.ws_token = ''
        if not self.connect():
            raise SungrowError(f"Can't connect to {self.sg_host}")
        self.logger.debug('Connected to %s', self.sg_host)

    # Basic methods
    def connect(self):
        '''
        Connect via WebSocket to the dongle, authenticate and fetch some information.

        :returns: True if connection succeeded, False otherwise
        '''
        # If already connected, reuse
        if self.ws_token != '':
            return True
        # Try to open the connection
        self.logger.debug('Connecting to %s', self.ws_endpoint)
        # Get a re-usable HTTP session
        self.session = requests.Session()
        # Connect to the websocket
        try:
            self.ws_socket = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
            self.ws_socket.connect(self.ws_endpoint, timeout=self.timeout)
        except Exception as err:
            self.logger.error('Websocket connection to %s failed - %s', self.ws_endpoint, err)
            return False
        self.logger.debug('Connected to %s', self.ws_endpoint)
        # Get a new token
        result = self.call(service='connect')
        self.ws_token = result.token
        # Need to authenticate immediately
        self.authenticate(self.config.admin_user, self.config.admin_passwd)
        # Get some basic information
        self.logger.debug('Requesting Device Information')
        result = self.call(service='devicelist', type='0', is_check_token='0')
        # Check that this is what we're expecting and set the device details
        self.inverter_id = None
        for d in result.list:
            if d['dev_type'] == 35:
                # Found the inverter
                self.inverter_id = str(d['dev_id'])
                self.inverter_code = str(d['dev_code'])
                self.inverter_model = d['dev_model']
                self.inverter_type = str(d['dev_type'])
            elif d['dev_type'] == 44:
                # Found the battery
                self.battery_id = str(d['dev_id'])
                self.battery_code = str(d['dev_code'])
                self.battery_model = d['dev_model']
                self.battery_type = str(d['dev_type'])
        if self.inverter_id is None:
            raise SungrowError(f"{self.sg_host} ({result.list[0]['dev_model']}) is not a hybrid inverter")
        return True

    def close(self):
        '''
        Properly close the websocket.

        :returns: True if the socket was open.
        '''
        if self.ws_socket is not None:
            self.logger.debug(f"Closing connection to {self.sg_host}")
            self.session.close()
            self.ws_socket.close()
            self.ws_socket = None
            self.ws_token = ''
            self.logger.debug('Closed connection to %s', {self.sg_host})
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
        except websocket.WebSocketTimeoutException:
            raise SungrowError(f"Timeout calling {kwargs['service']}")
        # Convert the reponse
        rdata = self._parse_response(r)
        self.logger.debug("Response %s", rdata)
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
        # And ignore the SSL certificate
        if 'verify' not in kwargs:
            kwargs['verify'] = False
        # Add the token to the params
        kwargs['params']['token'] = self.ws_token
        self.logger.debug('GET https://%s%s', self.sg_host, uri)
        try:
            r = self.session.get(f'https://{self.sg_host}{uri}', **kwargs)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            raise SungrowError(f"Time out while trying to access https://{self.sg_host}{uri}")
        if r.status_code != 200:
            raise SungrowError(f'Failed to access https://{self.sg_host}{uri} - {r.status_code} - {r.text}')
        # Convert the reponse
        rdata = self._parse_response(r.text)
        self.logger.debug("Response %s", rdata)
        return rdata

    def post(self, uri, **kwargs):
        '''
        Post something to the inverter. Automatically adds the token to the request.

        :param uri: Request uri (minus host and protocol)
        :param kwargs: additional requests.post arguments
        :returns: a ClassyDict containing the result_data.
        :raises: SungrowError if there was a problem.
        '''
        # Make sure there is a params argument
        if 'params' not in kwargs:
            kwargs['params'] = dict()
        # And a timeout arg
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        # And ignore the SSL certificate
        if 'verify' not in kwargs:
            kwargs['verify'] = False
        # Add the token to the params
        kwargs['params']['token'] = self.ws_token
        self.logger.debug('POST https://%s%s params=%s', self.sg_host, uri, kwargs['params'])
        try:
            r = self.session.post(f'https://{self.sg_host}{uri}', **kwargs)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            raise SungrowError(f"Time out while trying to access https://{self.sg_host}{uri}")
        if r.status_code != 200:
            raise SungrowError(f'Failed to access https://{self.sg_host}{uri} - {r.status_code} - {r.text}')
        return r.text

    def authenticate(self, username, password):
        '''
        Login to the inverter.
        '''
        result = self.call(service='login', passwd=password, username=username)
        self.ws_token = result.token

    def setParams(self, params):
        '''
        Set some parameter values on the inverter

        :param params: A Parameters object containing the registers that need to be set

        :returns: True if the setting worked
        '''
        result = self.call(
            service='param',
            dev_code=self.inverter_code,
            dev_type=self.inverter_type,
            devid_array=[self.inverter_id],
            type='9',
            count='1',
            list=params.dump()
        )
        # Check for success
        for r in result.list:
            if 'param_pid' not in r:
                self.logger.warning(f"Eh? Unexpected result from parameter setting - {result}")
            elif r['param_pid'] != -1 and r['result'] != 0:
                self.logger.warning(f"Failed to set {r}")
                return False
        return True

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
            raise SungrowError(f'Failed to parse the JSON response')
        if 'result_code' not in r or 'result_msg' not in r or 'result_data' not in r:
            raise SungrowError(f'Unexpected response - {r}')
        if r['result_code'] != 1:
            raise SungrowError(f'Received error response code {r["result_code"]} - {r["result_msg"]}')
        return ClassyDict(r['result_data'])
