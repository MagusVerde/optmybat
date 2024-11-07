#!/usr/bin/env python3
#
# Copyright 2024 Magus Verde
#
# A support module for Optmybat that supports network scanning to find
# and identify supported devices on the network.
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

# Import python libraries
import netaddr
from netifaces import gateways, interfaces, ifaddresses, AF_INET
import socket
import sys

# And then import my libraries
from util.classydict import ClassyDict
from sungrow.client import Client

# Define options for filtering the scans
SCAN_PHYSICAL_ONLY = 0x07
SCAN_NO_LOCAL = 0x01
SCAN_NO_VIRTUAL = 0x02
SCAN_NO_TUNNELS = 0x04
SCAN_EVERYTHING = 0

def getNetworkDetails(filter=SCAN_PHYSICAL_ONLY):
    '''
    Get the IPv4 network details of the local network.  Returns a list of
    ClassyDicts containing the address of each connected network
    '''
    # Collect information about the gateways for later use
    gws = gateways()
    (defaultGateway, defaultInterface) = gws['default'][AF_INET]
    gw_details = dict()
    for (addr, iface, default) in gws[AF_INET]:
        gw_details[iface] = addr
    # Loop over the interfaces creating a list of details
    bindings = []
    for ifaceName in interfaces():
        # Apply the various filters
        if filter & SCAN_NO_VIRTUAL and (ifaceName.startswith('virb') or ifaceName.startswith('vbox')):
            continue
        if filter & SCAN_NO_TUNNELS and (ifaceName.startswith('tap') or ifaceName.startswith('tun')):
            continue
        details = ifaddresses(ifaceName).setdefault(AF_INET)
        if details is None:
            continue
        details = details[0]
        if filter & SCAN_NO_LOCAL and details['addr'].startswith('127.'):
            continue
        # Add the interface name and the default gateway
        details['iface'] = ifaceName
        details['gateway'] = gw_details.get(ifaceName, defaultGateway)
        details['default_gw'] = ifaceName == defaultInterface
        # Use a ClassyDict because I hate constantly indexing dicts
        bindings.append(ClassyDict(details))
    # All done
    return bindings

def getNetworks(filter=SCAN_PHYSICAL_ONLY):
    '''
    ReturnCIDR strings for all attached networks.
    '''
    networks = []
    for network in getNetworkDetails(filter):
        networks.append(f"{network.addr}/{network.netmask}")
    return networks

def connect(address, port, timeout=None):
    '''
    Attempt to make a connection to the specified IP address and port.
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if timeout is not None:
        sock.settimeout(timeout)
    sock.connect((address, port))
    return sock

def tcpPing(target, port, timeout=0.01):
    '''
    Attempt to open a socket to the specified target and port.

    The default timeout is 10ms - good for a local connection but could
    be too short for a remote network
    '''
    try:
        sock = connect(target, port, timeout=timeout)
        sock.close()
        return True
    except (ConnectionRefusedError, TimeoutError):
        return False

def tcpScan(network, port):
    '''
    tcpPing each of the addresses in the specified network (addreess/mask)
    '''
    range = list(netaddr.IPNetwork(network))[1:-1]
    found = []
    for address in range:
        address = str(address)
        if tcpPing(address, port):
            found.append(address)
    return found

def sungrowScan(network):
    '''
    Scan the passed network for a Sungrow hybrid inverter

    :returns: a dict of addresses and inverter type
    '''
    hosts = {}
    for address in tcpScan(network, 443):
        # Check each web server to see if it's a Sungrow
        try:
            client = Client(host=address)
            hosts[address] = client.inverter_model
            if hasattr(client, 'battery_id'):
                hosts[address] += f" (battery is {client.battery_model})"
        except Exception as e:
            pass
    return hosts

def main(network):
    '''
    Scan a network for Sungrow inverters and print their
    addresses.

    :param network: a network to scan.  If None, determines
        the attached network and scans them.
    '''
    # Local the connected networks if needed
    if network is None:
        networks = getNetworks()
    else:
        networks = [ network ]
    # For each network, scan for a Sungrow inverter
    inverters = {}
    for n in networks:
        inverters.update(sungrowScan(n))
    # Print the results
    if len(inverters) == 0:
        print("Did not find any Sungrow hybrid inverters")
        sys.exit(1)
    else:
        for a in sorted(inverters.keys()):
            print(f"{a} -> {inverters[a]}")
        sys.exit(0)
