#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module handles creating the serial objects for the instrument classes.

This is needed for Windows because only 1 serial object can have an open
connection to a serial port at a time. This is not needed on Linux, as multiple
pyserial connections can be open at the same time to the same serial port.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import weakref
import serial

from instruments.abstract_instruments.comm import SerialCommunicator


# GLOBALS #####################################################################

# We want to only *weakly* hold references to serial ports, to allow for them
# to be deleted and reopened as need be.
#
# A WeakValueDictionary *will* delete entries when their values
# no longer exist. As a consequence, great care must be taken when iterating
# over the dictionary in any way.
# See http://docs.python.org/2/library/weakref.html#weakref.WeakValueDictionary
# for more details about what "great care" implies.
serialObjDict = weakref.WeakValueDictionary()

# METHODS #####################################################################


def new_serial_connection(port, baud=460800, timeout=3, write_timeout=3):
    """
    Return a `pyserial.Serial` connection object for the specified serial
    port address. The same object will be returned for identical port
    addresses. This is done for Windows which doesn't like when you have
    multiple things opening the same serial port. Typically this isn't a
    problem because you only have one instrument per serial port, but adapters
    such as the Galvant Industries GPIBUSB adapter can have multiple
    instruments on a single virtual serial port.

    :param str port: Port address for the serial port
    :param int baud: Baud rate for the serial port connection
    :param int timeout: Communication timeout for reading from the serial port
        connection. Units are seconds.
    :param write_timeout: Communication timeout for writing to the serial
        port connection. Units are seconds.
    :return: A :class:`SerialCommunicator` object wrapping the connection
    :rtype: `SerialCommunicator`
    """
    if not isinstance(port, str):
        raise TypeError('Serial port must be specified as a string.')

    if port not in serialObjDict or serialObjDict[port] is None:
        conn = SerialCommunicator(serial.Serial(
            port,
            baudrate=baud,
            timeout=timeout,
            writeTimeout=write_timeout
        ))
        serialObjDict[port] = conn
    # pylint: disable=protected-access
    if not serialObjDict[port]._conn.isOpen():
        serialObjDict[port]._conn.open()
    return serialObjDict[port]
