#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# socketwrapper.py: Wraps sockets into a filelike object.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
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

## IMPORTS #####################################################################

import io
import serial

import numpy as np
import quantities as pq

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class SerialWrapper(io.IOBase, AbstractCommunicator):
    """
    Wraps a pyserial Serial object to add a few properties as well as
    handling of termination characters.
    """
    
    def __init__(self, conn):
        AbstractCommunicator.__init__(self)
        
        if isinstance(conn, serial.Serial):
            self._conn = conn
            self._terminator = '\n'
            self._debug = False
            self._capture = False
        else:
            raise TypeError('SerialWrapper must wrap a serial.Serial object.')
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        return self._conn.port
    @address.setter
    def address(self, newval):
        # TODO: Input checking on Serial port newval
        # TODO: Add port changing capability to serialmanager
        # self._conn.port = newval
        raise NotImplementedError
        
    @property
    def terminator(self):
        return self._terminator
    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError('Terminator for SerialWrapper must be specified '
                              'as a single character string.')
        if len(newval) > 1:
            raise ValueError('Terminator for SerialWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
        
    @property
    def timeout(self):
        return self._conn.timeout * pq.second
    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second).rescale(pq.second).magnitude
        self._conn.timeout = newval

    @property
    def capture(self):
        return self._capture
    @capture.setter
    def capture(self, value):
        self._capture = value
        if value:
            self._capture_log = ""
    
        
    ## FILE-LIKE METHODS ##
    
    def close(self):
        try:
            self._conn.shutdown()
        finally:
            self._conn.close()
        
    def read(self, size):
        if (size >= 0):
            resp = self._conn.read(size)
            return resp
        elif (size == -1):
            result = bytearray()
            c = 0
            while c != self._terminator:
                c = self._conn.read(1)
                if c != self._terminator:
                    result += c
            return bytes(result)
        else:
            raise ValueError('Must read a positive value of characters.')
        
    def write(self, msg):
        if self._capture:
            self._capture_log += msg
        self._conn.write(msg)
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
        
    def flush_input(self):
        '''
        Instruct the wrapper to flush the input buffer, discarding the entirety
        of its contents.
        
        Calls the pyserial flushInput() method.
        '''
        self._conn.flushInput()
        
    ## METHODS ##
    
    def _sendcmd(self, msg):
        '''
        '''
        msg = msg + self._terminator
        self.write(msg)
        
    def _query(self, msg, size=-1):
        '''
        '''
        self.sendcmd(msg)
        return self.read(size)
        
