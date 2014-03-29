#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# serialManager.py: Manages open serial connections.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##
##


'''
This module handles creating the serial objects for the instrument classes.

This is needed for Windows because only 1 serial object can have an open
connection to a serial port at a time. This is not needed on Linux, as multiple 
pyserial connections can be open at the same time to the same serial port.
'''

## IMPORTS #####################################################################

import serial

from instruments.abstract_instruments.comm import SerialWrapper

# We want to only *weakly* hold references to serial ports, to allow for them
# to be deleted and reopened as need be.
import weakref

## GLOBALS #####################################################################

# Note that a WeakValueDictionary *will* delete entries when their values
# no longer exist. As a consequence, great care must be taken when iterating
# over the dictionary in any way.
# See http://docs.python.org/2/library/weakref.html#weakref.WeakValueDictionary
# for more details about what "great care" implies.
serialObjDict = weakref.WeakValueDictionary()

## METHODS #####################################################################

def newSerialConnection(port, baud=460800, timeout=3, writeTimeout=3):
    if not isinstance(port,str):
        raise TypeError('Serial port must be specified as a string.')
    
    if port not in serialObjDict or serialObjDict[port] is None:
        conn = SerialWrapper(serial.Serial(
                                         port,
                                         baudrate=baud,
                                         timeout=timeout,
                                         writeTimeout=writeTimeout
                                         ))
        serialObjDict[port] = conn
           # raise  'Serial connection error. Connection not added to serial \
           #     manager. Error message:{}'.format(e.strerror)
    if not serialObjDict[port]._conn.isOpen():
        serialObjDict[port]._conn.open()
    return serialObjDict[port]
    
